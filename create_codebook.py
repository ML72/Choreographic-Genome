import os
import json
import argparse
import numpy as np
import torch
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import MiniBatchKMeans
import smplx
from scipy.spatial.transform import Rotation as R
from tqdm import tqdm

def compute_features(poses, trans, smpl_model):
    """
    Computes frame-level behavioral features from SMPL parameters.
    Returns: F_t [N, D]
    """
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    smpl_model = smpl_model.to(device)
    
    # Use batch size to prevent OOM
    batch_size = 512
    all_joints = []
    
    with torch.no_grad():
        for i in range(0, poses.shape[0], batch_size):
            p = poses[i:i+batch_size].to(device)
            t = trans[i:i+batch_size].to(device)
            out = smpl_model(global_orient=p[:, :3], body_pose=p[:, 3:], transl=t)
            all_joints.append(out.joints.cpu())
            
    joints = torch.cat(all_joints, dim=0) # [N, J, 3]
    
    # 1. Strip Global Transform & Align Heading
    root_pos = joints[:, 0, :].clone()
    
    # Extract root heading (rotation around Y-axis)
    r_scipy = R.from_rotvec(poses[:, :3].numpy())
    euler = r_scipy.as_euler('XYZ', degrees=False)
    heading = euler[:, 1] # Y rotation
    
    # Create rotation matrices to inverse-rotate the heading (align to +Z)
    inv_heading_rot = R.from_euler('Y', -heading.reshape(-1, 1), degrees=False).as_matrix()
    inv_heading_rot = torch.from_numpy(inv_heading_rot).float()
    
    # Strip global X/Z translation (keep Y)
    root_pos_no_y = root_pos.clone()
    root_pos_no_y[:, 1] = 0 
    
    # Center joints to root X/Z and align heading
    local_joints = joints - root_pos_no_y.unsqueeze(1)
    local_joints = torch.einsum('nij,nkj->nki', inv_heading_rot, local_joints)
    
    # 2. Extract specific features
    # Joint velocities (local)
    joint_vels = torch.zeros_like(local_joints)
    joint_vels[1:] = local_joints[1:] - local_joints[:-1]
    joint_vels[0] = joint_vels[1]
    
    # Root Linear Velocity (local frame)
    root_vel = torch.zeros_like(root_pos)
    root_vel[1:] = root_pos[1:] - root_pos[:-1]
    root_vel[0] = root_vel[1]
    root_vel_local = torch.einsum('nij,nj->ni', inv_heading_rot, root_vel)
    
    # Root Angular Velocity (around Y)
    root_angular_vel = torch.zeros(poses.shape[0], 1)
    root_angular_vel[1:, 0] = torch.from_numpy(heading[1:] - heading[:-1])
    # Handle angle wrap-around
    root_angular_vel[root_angular_vel > np.pi] -= 2 * np.pi
    root_angular_vel[root_angular_vel < -np.pi] += 2 * np.pi
    root_angular_vel[0] = root_angular_vel[1]
    
    # Foot contact labels (Heuristic: foot velocity near 0)
    # Using typical SMPL foot joint indices: 7, 8, 10, 11
    foot_idx = [7, 8, 10, 11]
    global_foot_vels = torch.zeros((joints.shape[0], 4))
    global_foot_vels[1:] = torch.norm(joints[1:, foot_idx] - joints[:-1, foot_idx], dim=-1)
    global_foot_vels[0] = global_foot_vels[1]
    contacts = (global_foot_vels < 0.02).float()
    
    # Construct final feature vector F_t
    F_t = torch.cat([
        root_vel_local,                           # 3
        root_angular_vel,                         # 1
        local_joints.view(poses.shape[0], -1),    # 45*3 = 135
        joint_vels.view(poses.shape[0], -1),      # 45*3 = 135
        contacts                                  # 4
    ], dim=1) # ~278 dimensions for standard SMPL
    
    return F_t.numpy()

def create_windows(features, window_length):
    """
    Creates stride-1 sliding windows of length W from frame features.
    """
    N, D = features.shape
    if N < window_length:
        return np.empty((0, window_length * D))
    
    shape = (N - window_length + 1, window_length, D)
    strides = (features.strides[0], features.strides[0], features.strides[1])
    windows = np.lib.stride_tricks.as_strided(features, shape=shape, strides=strides)
    
    return windows.reshape(N - window_length + 1, -1)

def main():
    parser = argparse.ArgumentParser(description="Create Discretized Motion Codebook")
    parser.add_argument("--window_length", type=int, default=20, help="Temporal window length (frames)")
    parser.add_argument("--pca_num_samples", type=int, default=100_000, help="Number of samples for PCA")
    parser.add_argument("--pca_final_dim", type=int, default=64, help="PCA final projection dimension")
    parser.add_argument("--num_clusters", type=int, default=256, help="Number of KMeans clusters (codebook regions)")
    parser.add_argument("--region_order", type=str, choices=["pc1", "raw"], default="pc1", help="How region ids are assigned to clusters: pc1 ranks them along the first principal component, raw keeps arbitrary KMeans labels")
    parser.add_argument("--input_index", type=str, default=os.path.join("data", "index", "motion_index.npz"))
    parser.add_argument("--output_path", type=str, default=os.path.join("data", "index", "codebook.npz"))
    parser.add_argument("--smpl_dir", type=str, default=os.path.join("models"))
    parser.add_argument("--file_prefix", type=str, default=None, help="Build the vocabulary from only the source clips whose file name starts with this prefix (AIST++ encodes genre there, e.g. gJB for ballet jazz). Frames outside the subset are left unassigned.")
    args = parser.parse_args()
    
    print(f"Loading motion index from {args.input_index}...")
    data = np.load(args.input_index)
    poses = data['poses']
    trans = data['trans']
    file_indices = data['file_indices']
    num_total_frames = poses.shape[0]
    
    print("Loading SMPL model...")
    smpl_model = smplx.create(args.smpl_dir, model_type="smpl", ext="npz", gender="neutral")
    
    unique_files = np.unique(file_indices)

    # Optionally learn the vocabulary from one slice of the corpus only. This is
    # what makes a genre-specific instrument possible: everything downstream keys
    # off the tokens, and frames left at -1 are invisible to the engine, so the
    # body can only be realized from the chosen slice.
    if args.file_prefix:
        names_path = os.path.join(os.path.dirname(args.input_index), "file_names.json")
        with open(names_path, "r") as f:
            file_names = json.load(f)
        unique_files = np.array([fid for fid in unique_files
                                 if file_names[int(fid)].startswith(args.file_prefix)])
        print(f"Restricting vocabulary to {len(unique_files)} clips matching prefix '{args.file_prefix}'")
        if len(unique_files) == 0:
            print("Error: no clips match that prefix.")
            return
    
    all_windows = []
    window_frame_indices = []
    
    print("Extracting behavioral features and temporal windows...")
    for fid in tqdm(unique_files):
        mask = (file_indices == fid)
        idx_in_global = np.where(mask)[0]
        
        if len(idx_in_global) < args.window_length:
            continue
            
        p = torch.from_numpy(poses[mask]).float()
        t = torch.from_numpy(trans[mask]).float()
        
        feats = compute_features(p, t, smpl_model)
        windows = create_windows(feats, args.window_length)
        all_windows.append(windows)
        
        # Valid frames that get a full W-frame window mapping
        valid_idxs = idx_in_global[:len(idx_in_global) - args.window_length + 1]
        window_frame_indices.append(valid_idxs)
        
    if len(all_windows) == 0:
        print("Error: No valid clips found that are longer than the window length.")
        return
        
    X = np.concatenate(all_windows, axis=0, dtype=np.float32) # [Num_Valid_Frames, D_high]
    global_valid_idxs = np.concatenate(window_frame_indices, axis=0)
    
    print(f"Total valid windows extracted: {X.shape[0]} / {num_total_frames} frames")
    
    np.random.seed(42)
    num_samples = min(args.pca_num_samples, X.shape[0])
    sample_indices = np.random.choice(X.shape[0], num_samples, replace=False)
    X_sample = X[sample_indices]
    
    print("Fitting Scaler on subsample...")
    scaler = StandardScaler(copy=False)
    scaler.fit(X_sample)
    
    print("Fitting PCA on subsample...")
    pca = PCA(n_components=args.pca_final_dim, svd_solver='randomized', random_state=42)
    pca.fit(X_sample)
    
    del X_sample
    
    batch_size = 100_000
    N = X.shape[0]
    
    print("Scaling all data in batches...")
    for i in tqdm(range(0, N, batch_size), desc="Scaling"):
        X[i:i+batch_size] = scaler.transform(X[i:i+batch_size])
        
    print("PCA transforming all data in batches...")
    Z = np.empty((N, args.pca_final_dim), dtype=np.float32)
    for i in tqdm(range(0, N, batch_size), desc="PCA"):
        Z[i:i+batch_size] = pca.transform(X[i:i+batch_size]).astype(np.float32)
        
    del X
    
    print("Running MiniBatchKMeans quantization...")
    kmeans = MiniBatchKMeans(n_clusters=args.num_clusters, batch_size=1024, random_state=42)
    labels = kmeans.fit_predict(Z)
    centroids = kmeans.cluster_centers_
    
    # K-Means hands back cluster labels in an arbitrary order, so region 65 would
    # bear no kinematic relation to region 66. Because the downstream operator maps
    # byte value b straight onto region b, that arbitrariness would decide the look
    # of every dance. Ranking the centroids along the first principal component (the
    # dominant axis of variation in the windowed motion features, and axis 0 of the
    # PCA basis the centroids live in) makes region id a position on a real kinematic
    # axis, so nearby byte values name nearby gestures. This is a pure relabeling:
    # it re-indexes the vocabulary without changing the clustering.
    region_order = np.argsort(centroids[:, 0]).astype(np.int64)
    if args.region_order == "raw":
        region_order = np.arange(args.num_clusters, dtype=np.int64)
    forward = np.empty(args.num_clusters, dtype=np.int64)   # kmeans label -> region id
    forward[region_order] = np.arange(args.num_clusters)
    labels = forward[labels]
    centroids = centroids[region_order]
    
    # Initialize all frames to -1. The last W-1 frames of any clip will remain as -1
    final_tokens = np.full((num_total_frames,), -1, dtype=np.int32)
    final_tokens[global_valid_idxs] = labels
    
    print(f"Saving codebook to {args.output_path}...")
    os.makedirs(os.path.dirname(args.output_path), exist_ok=True)
    np.savez_compressed(
        args.output_path,
        tokens=final_tokens,
        kmeans_centroids=centroids,
        pca_components=pca.components_,
        pca_mean=pca.mean_,
        scaler_mean=scaler.mean_,
        scaler_scale=scaler.scale_,
        region_order=region_order,
        ordering=np.array(args.region_order)
    )
    print("Done!")

if __name__ == "__main__":
    main()
