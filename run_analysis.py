import os
import argparse
import random
import pickle
import glob
import json
import math
import heapq
import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt
from matplotlib import gridspec
from tqdm import tqdm
import smplx
import torch
import pyrender
import trimesh
import trimesh.transformations as tra

from generate_sample import generate_motion, dijkstra_shortest_path

def ensure_dirs():
    os.makedirs('results/plots', exist_ok=True)
    os.makedirs('results/metrics', exist_ok=True)

def levenshtein_distance(seq1, seq2):
    n, m = len(seq1), len(seq2)
    if n == 0: return m
    if m == 0: return n
    d = np.zeros((n + 1, m + 1))
    d[:, 0] = np.arange(n + 1)
    d[0, :] = np.arange(m + 1)
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = 0 if seq1[i-1] == seq2[j-1] else 1
            d[i, j] = min(
                d[i-1, j] + 1,     # deletion
                d[i, j-1] + 1,     # insertion
                d[i-1, j-1] + cost # substitution
            )
    return d[n, m]

def extract_ngrams(sequence, n):
    return [tuple(sequence[i:i+n]) for i in range(len(sequence)-n+1)]

def get_aist_transitions_and_energy(num_transitions):
    index_path = os.path.join("data", "index", "motion_index.npz")
    codebook_path = os.path.join("data", "index", "codebook.npz")
    
    index_data = np.load(index_path)
    poses = index_data['poses']
    trans = index_data['trans']
    file_indices = index_data['file_indices']
    
    codebook_data = np.load(codebook_path)
    tokens = codebook_data['tokens']
    
    valid_mask = (file_indices[:-1] == file_indices[1:])
    valid_mask = np.append(valid_mask, False)
    
    # Calculate kinetic energy (velocities)
    pose_vel = np.zeros_like(poses)
    trans_vel = np.zeros_like(trans)
    pose_vel[:-1][valid_mask[:-1]] = poses[1:][valid_mask[:-1]] - poses[:-1][valid_mask[:-1]]
    trans_vel[:-1][valid_mask[:-1]] = trans[1:][valid_mask[:-1]] - trans[:-1][valid_mask[:-1]]
    
    kinetic_energy = np.sum(pose_vel**2, axis=1) + np.sum(trans_vel**2, axis=1)
    
    # Extract sequences of valid regions
    sequences = []
    current_seq = []
    for i in range(len(tokens)):
        r = tokens[i]
        if r != -1:
            current_seq.append(r)
        if not valid_mask[i] or r == -1:
            if len(current_seq) > 1:
                sequences.append(current_seq)
            current_seq = []
            
    # Sample random sequences until we hit num_transitions
    sampled_seqs = []
    trans_count = 0
    sampled_energies = []
    
    random.shuffle(sequences)
    for seq in sequences:
        if trans_count >= num_transitions:
            break
        sampled_seqs.append(seq)
        trans_count += len(seq) - 1
        
    # Get 5 full contiguous sequences of kinetic energy for Plot 3
    aist_eval_energies = []
    unique_files = np.unique(file_indices)
    random.shuffle(unique_files)
    for uf in unique_files:
        if len(aist_eval_energies) >= 5: break
        idx = np.where((file_indices == uf) & valid_mask)[0]
        if len(idx) > 600:  # Valid length
            aist_eval_energies.append(kinetic_energy[idx][:600])

    return sampled_seqs, aist_eval_energies

def plot_upset(ax_bars, ax_matrix, aist_n, auto_n, text_n, title):
    set_names = ['AIST++', 'Auto', 'Text']
    
    only_aist = len(aist_n - auto_n - text_n)
    only_auto = len(auto_n - aist_n - text_n)
    only_text = len(text_n - aist_n - auto_n)
    a_and_a = len((aist_n & auto_n) - text_n)
    a_and_t = len((aist_n & text_n) - auto_n)
    u_and_t = len((auto_n & text_n) - aist_n)
    all_3 = len(aist_n & auto_n & text_n)
    
    intersections = [
        ((1,0,0), only_aist),
        ((0,1,0), only_auto),
        ((0,0,1), only_text),
        ((1,1,0), a_and_a),
        ((1,0,1), a_and_t),
        ((0,1,1), u_and_t),
        ((1,1,1), all_3)
    ]
    intersections.sort(key=lambda x: x[1], reverse=True)
    
    sizes = [x[1] for x in intersections]
    matrices = [x[0] for x in intersections]
    
    x = np.arange(len(sizes))
    colors = plt.cm.tab10.colors[:len(sizes)]
    ax_bars.bar(x, sizes, color=colors)
    ax_bars.set_title(title, pad=20)
    ax_bars.set_ylabel("Intersection Size")
    ax_bars.set_xticks([])
    
    # Hide borders
    for spine in ['top', 'right', 'bottom']:
        ax_bars.spines[spine].set_visible(False)
        
    ax_matrix.set_ylim(-0.5, len(set_names)-0.5)
    ax_matrix.set_xlim(-0.5, len(sizes)-0.5)
    ax_matrix.set_yticks(np.arange(len(set_names)))
    ax_matrix.set_yticklabels(set_names)
    ax_matrix.set_xticks([])
    
    for i, combination in enumerate(matrices):
        y_coords = []
        for r, in_set in enumerate(combination):
            if in_set:
                ax_matrix.scatter(i, r, color='black', s=100, zorder=5)
                y_coords.append(r)
            else:
                ax_matrix.scatter(i, r, color='lightgray', s=100, zorder=5)
        if len(y_coords) > 1:
            ax_matrix.plot([i, i], [min(y_coords), max(y_coords)], color='black', lw=2, zorder=4)
            
    for spine in ['top', 'right', 'bottom', 'left']:
        ax_matrix.spines[spine].set_visible(False)

def run_part_1():
    print("Running Part 1: Stylistic & Art-Side Evaluation")
    
    # 1. Gather AIST++ transitions
    print("Gathering Original AIST++ data...")
    aist_seqs, aist_energy = get_aist_transitions_and_energy(5000)
    aist_ngrams_3 = set(ng for seq in aist_seqs for ng in extract_ngrams(seq, 3))
    aist_ngrams_4 = set(ng for seq in aist_seqs for ng in extract_ngrams(seq, 4))
    
    # 2. Gather Autonomous Mode transitions
    print("Generating Autonomous Mode sequences...")
    auto_seqs = []
    auto_eval_energies = []
    auto_trans_count = 0
    idx = 0

    with tqdm(total=5000, desc="Autonomous") as pbar:
        while auto_trans_count < 5000:
            run_data, g_poses, g_trans = generate_motion(
                num_frames=720, 
                run_name=f"auto_{idx}", 
                gender='neutral', 
                physics_algorithms_on=False, 
                render_video=False, 
                verbose=False
            )
            regions = [int(x) for x in run_data["executed_dna"].split(',') if x.strip()]
            auto_seqs.append(regions)
            
            added_tc = max(0, len(regions) - 1)
            auto_trans_count += added_tc
            pbar.update(added_tc)
            
            if len(auto_eval_energies) < 5 and len(g_poses) > 600:
                ke = np.sum(np.diff(g_poses[:601], axis=0)**2, axis=1) + np.sum(np.diff(g_trans[:601], axis=0)**2, axis=1)
                auto_eval_energies.append(ke)
                
            idx += 1
        
    # 3. Gather Text-Guided Mode transitions
    print("Generating Text-Guided Mode sequences...")
    txt_files = glob.glob('data/eval_text/*.txt')
    lines = []
    for tf in txt_files:
        with open(tf, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    lines.append(line)
    random.shuffle(lines)
    
    text_seqs = []
    text_eval_energies = []
    text_trans_count = 0
    txt_all_en_list = []
    idx = 0
    
    with tqdm(total=5000, desc="Text-Guided") as pbar:
        while text_trans_count < 5000 and idx < len(lines):
            line = lines[idx]
            idx += 1
            if len(text_eval_energies) < 5 and len(line) >= 20:
                line_to_use = line[:20]
            else:
                line_to_use = line
                
            # Run without rendering or physics filtering (for speed of dataset collection)
            run_data, g_poses, g_trans = generate_motion(num_frames=0, run_name=f"text_{idx}", input_text=line_to_use, render_video=False, physics_algorithms_on=False, verbose=False)
            regions = [int(x) for x in run_data["executed_dna"].split(',') if x.strip()]
            text_seqs.append(regions)
            
            added_tc = max(0, len(regions) - 1)
            text_trans_count += added_tc
            pbar.update(added_tc)
            
            # extract whole curves up to 5
            if len(g_poses) > 1:
                ke_all = np.sum(np.diff(g_poses, axis=0)**2, axis=1) + np.sum(np.diff(g_trans, axis=0)**2, axis=1)
                txt_all_en_list.append(ke_all)
            
            if len(text_eval_energies) < 5 and len(line) >= 20 and len(g_poses) > 600:
                ke = np.sum(np.diff(g_poses[:601], axis=0)**2, axis=1) + np.sum(np.diff(g_trans[:601], axis=0)**2, axis=1)
                text_eval_energies.append(ke)
                
    # Metric: Choreographic N-Gram Novelty
    text_ngrams_3 = set(ng for seq in text_seqs for ng in extract_ngrams(seq, 3))
    text_ngrams_4 = set(ng for seq in text_seqs for ng in extract_ngrams(seq, 4))
    
    novel_3 = text_ngrams_3 - aist_ngrams_3
    novel_4 = text_ngrams_4 - aist_ngrams_4
    
    perc_novel_3 = len(novel_3) / max(1, len(text_ngrams_3)) * 100
    perc_novel_4 = len(novel_4) / max(1, len(text_ngrams_4)) * 100
    
    # Metric: Sequence Edit Distance (determinism vs diversity)
    # pair 100 random text seqs
    distances = []
    sub_text_seqs = random.sample(text_seqs, min(100, len(text_seqs)))
    for i in range(len(sub_text_seqs)):
        for j in range(i+1, len(sub_text_seqs)):
            distances.append(levenshtein_distance(sub_text_seqs[i], sub_text_seqs[j]))
            
    avg_edit_dist = np.mean(distances) if distances else 0.0
    
    aist_all_en = np.concatenate(aist_energy) if len(aist_energy) else [0]
    txt_all_en = np.concatenate(txt_all_en_list) if len(txt_all_en_list) else [0]
    
    # Save metrics
    with open('results/metrics/part_1.txt', 'w') as f:
        f.write(f"Choreographic 3-Gram Novelty: {perc_novel_3:.2f}%\n")
        f.write(f"Choreographic 4-Gram Novelty: {perc_novel_4:.2f}%\n")
        f.write(f"Average Sequence Edit Distance (100 samples): {avg_edit_dist:.2f}\n")
        f.write(f"AIST++ Mean Kinetic Energy: {np.mean(aist_all_en):.4f}\n")
        f.write(f"Text-Guided Mean Kinetic Energy: {np.mean(txt_all_en):.4f}\n")
        
    print("Saving plots...")
    # Plot 1: Codebook Identity Grids
    index_path = os.path.join("data", "index", "motion_index.npz")
    codebook_path = os.path.join("data", "index", "codebook.npz")
    poses = np.load(index_path)['poses']
    tokens = np.load(codebook_path)['tokens']
    
    fig_grid = plt.figure(figsize=(20, 10))
    fig_grid.suptitle("Codebook Identity Grids (Regions 0-4)\nMale (Blue) | Female (Pink) | Neutral (Purple)", fontsize=16)
    
    # Render setup
    os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
    scene = pyrender.Scene(ambient_light=(0.6, 0.6, 0.6), bg_color=[1.0, 1.0, 1.0, 1.0])
    camera = pyrender.PerspectiveCamera(yfov=np.pi / 3.0)
    
    key_light = pyrender.DirectionalLight(color=[1.0, 0.95, 0.9], intensity=2.5)
    kl_pose = np.eye(4); kl_pose[:3, :3] = tra.euler_matrix(np.radians(-45), np.radians(45), 0)[:3, :3]
    scene.add(key_light, pose=kl_pose)
    fill_light = pyrender.DirectionalLight(color=[0.9, 0.95, 1.0], intensity=1.2)
    fl_pose = np.eye(4); fl_pose[:3, :3] = tra.euler_matrix(np.radians(-30), np.radians(-45), 0)[:3, :3]
    scene.add(fill_light, pose=fl_pose)
    back_light = pyrender.DirectionalLight(color=[1.0, 1.0, 1.0], intensity=2.0)
    bl_pose = np.eye(4); bl_pose[:3, :3] = tra.euler_matrix(np.radians(-135), np.radians(0), 0)[:3, :3]
    scene.add(back_light, pose=bl_pose)

    cam_pose = np.eye(4) @ tra.rotation_matrix(np.radians(-15 * np.pi / 180), [1, 0, 0])
    cam_pose[1, 3] = 0.1
    cam_pose[2, 3] = 2.2
    cam_node = scene.add(camera, pose=cam_pose)

    # Base models
    smpl_models = {
        'male': smplx.create("models", model_type='smpl', gender='male', batch_size=1),
        'female': smplx.create("models", model_type='smpl', gender='female', batch_size=1),
        'neutral': smplx.create("models", model_type='smpl', gender='neutral', batch_size=1)
    }
    mats = {
        'male': pyrender.MetallicRoughnessMaterial(baseColorFactor=[0.2, 0.4, 0.8, 1.0], metallicFactor=0.2, roughnessFactor=0.6, doubleSided=True),
        'female': pyrender.MetallicRoughnessMaterial(baseColorFactor=[0.9, 0.3, 0.6, 1.0], metallicFactor=0.2, roughnessFactor=0.6, doubleSided=True),
        'neutral': pyrender.MetallicRoughnessMaterial(baseColorFactor=[0.5, 0.2, 0.8, 1.0], metallicFactor=0.2, roughnessFactor=0.6, doubleSided=True)
    }
    renderer = pyrender.OffscreenRenderer(viewport_width=300, viewport_height=300)
    
    for r in tqdm(range(5), desc="Rendering Codebook Poses"):
        region_idx = np.where(tokens == r)[0]
        if len(region_idx) == 0: continue
        sampled_i = np.random.choice(region_idx, size=min(9, len(region_idx)), replace=False)
        
        genders = ['male'] * 3 + ['female'] * 3 + ['neutral'] * 3
        np.random.shuffle(genders)
        
        # Add label in the first spot
        ax_label = fig_grid.add_subplot(5, 10, r*10 + 1)
        ax_label.text(0.5, 0.5, f"Region {r}", ha='center', va='center', fontsize=14)
        ax_label.set_axis_off()
        
        for c, i in enumerate(sampled_i):
            gender = genders[c]
            
            p = torch.tensor(poses[i:i+1], dtype=torch.float32)
            out = smpl_models[gender](global_orient=p[:,:3], body_pose=p[:,3:], transl=torch.zeros((1,3)))
            vertices = out.vertices.detach().cpu().numpy().squeeze()
            faces = smpl_models[gender].faces
            
            mesh = trimesh.Trimesh(vertices, faces)
            mesh_node = pyrender.Mesh.from_trimesh(mesh, material=mats[gender], smooth=True)
            node = scene.add(mesh_node)
            
            color, _ = renderer.render(scene, flags=pyrender.RenderFlags.RGBA)
            scene.remove_node(node)
            
            ax = fig_grid.add_subplot(5, 10, r*10 + c + 2)
            ax.imshow(color)
            ax.set_xticks([])
            ax.set_yticks([])
            for spine in ax.spines.values():
                spine.set_edgecolor('black')
                spine.set_linewidth(1)

    renderer.delete()
    plt.tight_layout()
    plt.savefig("results/plots/plot_1_codebook_grid.png", dpi=150)
    plt.close()
    
    # Plot 2: UpSet Plot
    auto_ngrams_3 = set(ng for seq in auto_seqs for ng in extract_ngrams(seq, 3))
    auto_ngrams_4 = set(ng for seq in auto_seqs for ng in extract_ngrams(seq, 4))
    
    fig = plt.figure(figsize=(15, 6))
    gs = fig.add_gridspec(2, 2, height_ratios=[3, 1], hspace=0.1)
    
    ax_bar_3 = fig.add_subplot(gs[0, 0])
    ax_mat_3 = fig.add_subplot(gs[1, 0], sharex=ax_bar_3)
    plot_upset(ax_bar_3, ax_mat_3, aist_ngrams_3, auto_ngrams_3, text_ngrams_3, "Unique 3-Gram Sequence Overlap")
    
    ax_bar_4 = fig.add_subplot(gs[0, 1])
    ax_mat_4 = fig.add_subplot(gs[1, 1], sharex=ax_bar_4)
    plot_upset(ax_bar_4, ax_mat_4, aist_ngrams_4, auto_ngrams_4, text_ngrams_4, "Unique 4-Gram Sequence Overlap")
    
    plt.savefig("results/plots/plot_2_phrase_overlap.png", dpi=150)
    plt.close()
    
    # Plot 3: Rhythmic Envelope (Time Series)
    plt.figure(figsize=(12, 6))
    
    colors = {'AIST++': '#1f77b4', 'Autonomous': '#ff7f0e', 'Text-Guided': '#2ca02c'}
    
    def plot_lines(arr_list, label, color):
        for i, arr in enumerate(arr_list):
            if len(arr) < 600: continue
            custom_label = label if i == 0 else ""
            plt.plot(np.arange(600), arr[:600], color=color, linewidth=1.2, alpha=0.7, label=custom_label)

    plot_lines(aist_energy, 'AIST++', colors['AIST++'])
    plot_lines(auto_eval_energies, 'Autonomous', colors['Autonomous'])
    plot_lines(text_eval_energies, 'Text-Guided', colors['Text-Guided'])
    
    plt.yscale('log')
    plt.title("Kinetic Signature (Kinetic Energy over Time)")
    plt.xlabel("Time (Frames)")
    plt.ylabel("Kinetic Energy (Squared Velocity Sum)")
    plt.legend()
    plt.tight_layout()
    plt.savefig("results/plots/plot_3_rhythmic_envelope.png", dpi=150)
    plt.close()

def run_part_2():
    print("Running Part 2: Structural Graph Traversability")
    graph_path = os.path.join("data", "index", "plausibility_graph.pkl")
    with open(graph_path, 'rb') as f:
        graph = pickle.load(f)
        
    num_nodes = 256
    num_possible_edges = num_nodes * (num_nodes - 1)
    num_edges = sum(len(graph.get(k, {})) for k in range(num_nodes))
    density = num_edges / num_possible_edges if num_possible_edges > 0 else 0
    
    alphanumeric = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    alpha_regions = [ord(c) for c in alphanumeric]
    
    failures = 0
    total_alpha_pairs = 0
    for i in tqdm(alpha_regions, desc="Alphanumeric Regions"):
        for j in alpha_regions:
            if i != j:
                total_alpha_pairs += 1
                path = dijkstra_shortest_path(graph, i, j)
                if not path:
                    failures += 1
                    
    fail_rate = (failures / total_alpha_pairs) * 100 if total_alpha_pairs > 0 else 0
    
    # Average Dijkstra bridges
    sampled_pairs = []
    nodes = list(range(256))
    for _ in range(10000):
        n1, n2 = random.sample(nodes, 2)
        sampled_pairs.append((n1, n2))
        
    bridges_dist = []
    # Using progress bar
    for n1, n2 in tqdm(sampled_pairs, desc="Dijkstra Sampling"):
        path = dijkstra_shortest_path(graph, n1, n2)
        if path:
            # path is e.g. [inter1, inter2, target].
            # original prompt length to add was intermediate bridges. 
            # if direct, path is [target], length 1. So bridges = len(path) - 1
            bridges_dist.append(len(path) - 1)
            
    avg_bridges = np.mean(bridges_dist) if bridges_dist else 0
    
    with open('results/metrics/part_2.txt', 'w') as f:
        f.write(f"Graph Density: {density:.6f}\n")
        f.write(f"Alphanumeric Pathfinding Failure Rate: {fail_rate:.2f}%\n")
        f.write(f"Average Dijkstra Bridges per Region Transition: {avg_bridges:.2f}\n")
        
    # Plot 4: Bridge Density per Region Transition
    plt.figure(figsize=(10, 6))
    counts = np.bincount(bridges_dist)
    x = np.arange(len(counts))
    plt.bar(x, counts / np.sum(counts), color='#9467bd')
    plt.title("Bridge Density per Region Transition")
    plt.xlabel("Number of Intermediate Bridges Injected")
    plt.ylabel("Relative Frequency")
    plt.xticks(x)
    plt.tight_layout()
    plt.savefig("results/plots/plot_4_bridge_density.png", dpi=150)
    plt.close()

def compute_mesh_stats(poses_list, trans_list):
    if len(poses_list) == 0:
        return {}
        
    body_model = smplx.create("models", model_type='smpl', gender='neutral', batch_size=1)
    
    all_fpe = []
    skating_errors = []
    jerks = []
    
    # Analyze essentially as sequences
    for i in tqdm(range(len(poses_list)), desc="Mesh Stats"):
        poses = torch.tensor(poses_list[i], dtype=torch.float32)
        trans = torch.tensor(trans_list[i], dtype=torch.float32)
        
        # Batch size needs to match
        local_body = smplx.create("models", model_type='smpl', gender='neutral', batch_size=poses.shape[0])
        out = local_body(global_orient=poses[:,:3], body_pose=poses[:,3:], transl=trans)
        
        v = out.vertices.detach().numpy()
        j = out.joints.detach().numpy()
        
        # FPE: mesh clipping below Y=0
        min_y = np.min(v[:, :, 1], axis=1)
        fpe_clip = np.clip(-min_y, 0, None)
        all_fpe.extend(fpe_clip)
        
        # FSR: horizontal foot slippage during planted states (Y < 2cm)
        foot_joints = j[:, [7, 8, 10, 11], :]
        for f in range(4):
            vel = np.linalg.norm(np.diff(foot_joints[:, f, :], axis=0), axis=-1)
            # Find planted frames. Approximate Y < 2cm
            # Note: joints are inside the foot volume, typically ~4-8cm above the floor.
            # We relax the threshold to 0.08m (8cm) to reliably capture planted joints, 
            # since a true y_height of 2cm strictly applies to surface meshes, not bone joints.
            y_heights = foot_joints[:-1, f, 1]
            planted = y_heights < 0.08
            if np.any(planted):
                # Calculate horizontal sliding in planted frame
                xz_vel = np.linalg.norm(np.diff(foot_joints[:, f, [0, 2]], axis=0), axis=-1)
                skating_errors.extend(xz_vel[planted])
                
        # Jerk (3rd derivative)
        if len(trans) > 3:
            vel = np.diff(trans.numpy(), axis=0)
            acc = np.diff(vel, axis=0)
            jerk = np.diff(acc, axis=0)
            j_mag = np.linalg.norm(jerk, axis=-1)
            jerks.extend(j_mag)
            
    return {
        "FPE": all_fpe,
        "Skating": skating_errors,
        "Jerk": jerks
    }

def print_stats(name, data_dict, f):
    f.write(f"--- {name} ---\n")
    for k, v in data_dict.items():
        if len(v) == 0:
            f.write(f"  {k}: No data\n")
            continue
        v_np = np.array(v)
        f.write(f"  {k} - Mean: {np.mean(v_np):.5f}, Median: {np.median(v_np):.5f}, Min: {np.min(v_np):.5f}, Max: {np.max(v_np):.5f}, SD: {np.std(v_np):.5f}\n")

def run_part_3():
    print("Running Part 3: System Polish & Quality Assurance")
    
    # 1. Gather original AIST++ 10 sequences x 1000 frames
    index_path = os.path.join("data", "index", "motion_index.npz")
    index_data = np.load(index_path)
    poses = index_data['poses']
    trans = index_data['trans']
    file_indices = index_data['file_indices']
    
    valid_mask = (file_indices[:-1] == file_indices[1:])
    valid_mask = np.append(valid_mask, False)
    
    aist_poses = []
    aist_trans = []
    
    v_indices = np.where(valid_mask)[0]
    for _ in range(10):
        start = random.choice(v_indices[:-1000])
        if file_indices[start] == file_indices[start+999] and np.all(valid_mask[start:start+1000]):
            aist_poses.append(poses[start:start+1000])
            aist_trans.append(trans[start:start+1000])
            
    aist_stats = compute_mesh_stats(aist_poses, aist_trans)
    
    # 2. Autonomous W/O Physics
    print("Generating Autonomous Mode sequences Without Physics...")
    auto_np_poses = []
    auto_np_trans = []
    for i in tqdm(range(10), desc="Bench NP"):
        _, p, t = generate_motion(1000, f"bench_np_{i}", gender='neutral', physics_algorithms_on=False, render_video=False, verbose=False)
        auto_np_poses.append(p)
        auto_np_trans.append(t)
    auto_np_stats = compute_mesh_stats(auto_np_poses, auto_np_trans)
    
    # 3. Autonomous WITH Physics
    print("Generating Autonomous Mode sequences With Physics...")
    auto_wp_poses = []
    auto_wp_trans = []
    for i in tqdm(range(10), desc="Bench WP"):
        _, p, t = generate_motion(1000, f"bench_wp_{i}", gender='neutral', physics_algorithms_on=True, render_video=False, verbose=False)
        auto_wp_poses.append(p)
        auto_wp_trans.append(t)
    auto_wp_stats = compute_mesh_stats(auto_wp_poses, auto_wp_trans)
    
    with open('results/metrics/part_3.txt', 'w') as f:
        print_stats("AIST++ Original", aist_stats, f)
        print_stats("Autonomous Without Physics", auto_np_stats, f)
        print_stats("Autonomous With Physics", auto_wp_stats, f)


# =========================================================================== #
#  Part 4: Artistic Case Studies (Structural Amplification)
# --------------------------------------------------------------------------- #
#  Rather than re-running the heavyweight ML benchmarks, Part 4 treats a small,
#  deliberately heterogeneous corpus of culturally and structurally significant
#  texts as input to the byte->codebook->choreography pipeline, and visualizes
#  the "choreographic genome" each text produces.
#
#  The point is NOT classification accuracy; it is amplification: the system
#  turns up the signal on the structural patterns that conventional,
#  semantics-first generation discards. Each byte of each text maps to one of
#  256 motion codebook regions; we then measure how much embodied movement the
#  body must traverse to physically realize that text, and how distinct each
#  text's genome is.
#
#  Outputs (under results/plots and results/metrics):
#    - plot_5_choreographic_genome.png : stacked region-strip "genomes" per text
#    - plot_6_amplification.png        : structural-amplification metrics
#    - case_studies.txt (+ .json)      : machine-readable metrics
#
#  This is intentionally lightweight: it loads ONLY the precomputed plausibility
#  graph (a few hundred KB), not the multi-GB motion index, so it runs in
#  seconds.
# =========================================================================== #

GENOME_CMAP = "turbo"  # high-contrast, perceptually ordered map over region ids 0-255


# Curated corpus. Each entry: key -> (category, short label, raw text). Chosen to
# span the loud Western canon, the overlooked machine voice, marginalized and
# Indigenous scripts silenced by ASCII-centric computing, and the boundary
# between signal and noise.
CASE_STUDIES = {
    "canon": (
        "Literary canon",
        "Shakespeare, Sonnet 18",
        "Shall I compare thee to a summer's day?",
    ),
    "machine": (
        "Machine exhaust",
        "Python traceback",
        'Traceback (most recent call last): File "app.py", line 42, in <module>',
    ),
    "code": (
        "Source code",
        "A line of Python",
        "for i in range(256): codebook[i] = kmeans.predict(x)",
    ),
    "devanagari": (
        "Non-Latin script",
        "Hindi (Devanagari): \"main nachta hoon\" / I dance",
        "मैं नाचता हूँ",
    ),
    "cherokee": (
        "Indigenous script",
        "Cherokee syllabary: \"Tsalagi\"",
        "ᏣᎳᎩ ᎦᏬᏂᎯᏍᏗ",
    ),
    "marginalized": (
        "Marginalized voice",
        "Sojourner Truth, 1851",
        "Ain't I a woman?",
    ),
    "signal": (
        "Signal vs. noise",
        "SOS, in Morse",
        "... --- ...",
    ),
}

# Order controls top-to-bottom placement in the genome figure.
ORDER = ["canon", "marginalized", "devanagari", "cherokee", "code", "machine", "signal"]


def dijkstra_path(graph, start, target):
    """Shortest path over the plausibility graph. Returns the list of nodes
    AFTER start up to and including target (so direct edge -> [target],
    same node -> [], unreachable -> [])."""
    if start == target:
        return []
    queue = [(0.0, start, [])]
    visited = set()
    while queue:
        cost, node, path = heapq.heappop(queue)
        if node == target:
            return path
        if node not in visited:
            visited.add(node)
            for neighbor, weight in graph.get(node, {}).items():
                if neighbor not in visited:
                    heapq.heappush(queue, (cost + weight, neighbor, path + [neighbor]))
    return []


def levenshtein(a, b):
    n, m = len(a), len(b)
    if n == 0:
        return m
    if m == 0:
        return n
    prev = list(range(m + 1))
    for i in range(1, n + 1):
        cur = [i] + [0] * m
        for j in range(1, m + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
        prev = cur
    return prev[m]


def shannon_entropy(values):
    if not values:
        return 0.0
    counts = {}
    for v in values:
        counts[v] = counts.get(v, 0) + 1
    total = len(values)
    return -sum((c / total) * math.log2(c / total) for c in counts.values())


def analyze():
    graph_path = os.path.join("data", "index", "plausibility_graph.pkl")
    with open(graph_path, "rb") as f:
        graph = pickle.load(f)

    records = {}
    for key in ORDER:
        category, label, text = CASE_STUDIES[key]
        raw = text.strip()
        byte_seq = list(raw.encode("utf-8"))      # each byte -> a region id in [0,255]
        regions = byte_seq                        # target choreographic DNA

        # How much embodied movement must the body traverse to honor this text?
        # For every adjacent pair of target regions we ask the plausibility graph
        # how many physical "bridge" regions are needed to connect them safely.
        bridges = 0
        unreachable = 0
        for a, b in zip(regions[:-1], regions[1:]):
            if a == b:
                continue
            path = dijkstra_path(graph, a, b)
            if path:
                bridges += len(path) - 1          # intermediate bridge regions
            else:
                unreachable += 1                  # needs nearest-region proxy substitution

        n_chars = len(raw)
        n_bytes = len(byte_seq)
        traversed = n_bytes + bridges             # total regions the body steps through
        records[key] = {
            "category": category,
            "label": label,
            "text": raw,
            "regions": regions,
            "n_chars": n_chars,
            "n_bytes": n_bytes,
            "unique_regions": len(set(regions)),
            "region_entropy_bits": shannon_entropy(regions),
            "bridges": bridges,
            "unreachable": unreachable,
            "regions_traversed": traversed,
            # amplification factor: motion regions the body traverses per *character*
            # of source text. ASCII canon ~1.0+bridges; multibyte scripts amplify.
            "amplification_per_char": traversed / max(1, n_chars),
            "bytes_per_char": n_bytes / max(1, n_chars),
        }

    # Pairwise structural divergence of the genomes (determinism + distinctness).
    keys = ORDER
    div = np.zeros((len(keys), len(keys)))
    for i, ki in enumerate(keys):
        for j, kj in enumerate(keys):
            div[i, j] = levenshtein(records[ki]["regions"], records[kj]["regions"])

    return records, div


def plot_genome(records):
    keys = ORDER
    fig = plt.figure(figsize=(13, 7.2))
    gs = gridspec.GridSpec(len(keys), 1, hspace=0.75, left=0.30, right=0.97,
                           top=0.92, bottom=0.13)

    max_len = max(len(records[k]["regions"]) for k in keys)

    for row, k in enumerate(keys):
        rec = records[k]
        ax = fig.add_subplot(gs[row])
        strip = np.array(rec["regions"]).reshape(1, -1)
        ax.imshow(strip, aspect="auto", cmap=GENOME_CMAP, vmin=0, vmax=255,
                  extent=[0, len(rec["regions"]), 0, 1], interpolation="nearest")
        # uniform x-scale across rows so length differences are legible;
        # headroom on the right keeps the longest strip's annotation on-canvas
        ax.set_xlim(0, max_len * 1.18)
        ax.set_yticks([])
        ax.set_xticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)

        # left-hand annotation: category + readable label, both kept inside the
        # strip's own vertical band so they unambiguously attach to this row
        ax.text(-0.012 * max_len, 0.70, rec["category"], ha="right", va="center",
                fontsize=11, transform=ax.transData)
        ax.text(-0.012 * max_len, 0.24, rec["label"], ha="right", va="center",
                fontsize=7.5, style="italic", color="#444444", transform=ax.transData)
        # right-hand annotation: regions traversed
        ax.text(len(rec["regions"]) + 0.008 * max_len, 0.5,
                f"{rec['regions_traversed']} regions",
                ha="left", va="center", fontsize=8, color="#222222",
                transform=ax.transData)

    fig.suptitle("The choreographic genome: each text amplified into a sequence of motion regions",
                 fontsize=13, y=0.985)

    # shared colorbar describing the region encoding
    cax = fig.add_axes([0.30, 0.065, 0.67, 0.016])
    sm = plt.cm.ScalarMappable(cmap=GENOME_CMAP,
                               norm=plt.Normalize(vmin=0, vmax=255))
    cb = fig.colorbar(sm, cax=cax, orientation="horizontal")
    cb.set_label("Motion codebook region id (one per text byte)", fontsize=9)
    cb.ax.tick_params(labelsize=8)

    out = os.path.join("results", "plots", "plot_5_choreographic_genome.png")
    plt.savefig(out, dpi=200)
    plt.close()
    print(f"Saved {out}")


def plot_amplification(records):
    keys = ORDER
    cats = [records[k]["category"] for k in keys]
    amp = [records[k]["amplification_per_char"] for k in keys]
    ent = [records[k]["region_entropy_bits"] for k in keys]
    bpc = [records[k]["bytes_per_char"] for k in keys]

    colors = plt.cm.turbo(np.linspace(0.08, 0.92, len(keys)))
    y = np.arange(len(keys))[::-1]  # first key on top

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.0))

    # Panel 1: amplification factor (regions traversed per character), with the
    # multibyte (non-Latin) component highlighted.
    ax1.barh(y, amp, color=colors, edgecolor="white")
    for yi, k in zip(y, keys):
        bpcv = records[k]["bytes_per_char"]
        if bpcv > 1.05:  # non-ASCII: more than one byte (hence region) per glyph
            ax1.annotate(f"{bpcv:.1f} bytes/glyph",
                         (records[k]["amplification_per_char"], yi),
                         xytext=(4, 0), textcoords="offset points",
                         va="center", fontsize=8, color="#333333")
    ax1.set_yticks(y)
    ax1.set_yticklabels(cats, fontsize=10)
    ax1.set_xlabel("Motion regions traversed per character (amplification factor)", fontsize=10)
    ax1.set_title("Texts marginalized by ASCII are amplified into more movement", fontsize=11)
    for s in ["top", "right"]:
        ax1.spines[s].set_visible(False)

    # Panel 2: structural entropy of the genome (how varied the movement is)
    ax2.barh(y, ent, color=colors, edgecolor="white")
    ax2.set_yticks(y)
    ax2.set_yticklabels([records[k]["label"] for k in keys], fontsize=8)
    ax2.set_xlabel("Region-distribution entropy (bits)", fontsize=10)
    ax2.set_title("Each text carries a distinct structural signature", fontsize=11)
    for s in ["top", "right"]:
        ax2.spines[s].set_visible(False)

    plt.tight_layout()
    out = os.path.join("results", "plots", "plot_6_amplification.png")
    plt.savefig(out, dpi=200)
    plt.close()
    print(f"Saved {out}")


def write_metrics(records, div):
    os.makedirs(os.path.join("results", "metrics"), exist_ok=True)
    out = os.path.join("results", "metrics", "case_studies.txt")
    with open(out, "w", encoding="utf-8") as f:
        f.write("Artistic Case Studies — Structural Amplification Metrics\n")
        f.write("=" * 60 + "\n\n")
        for k in ORDER:
            r = records[k]
            f.write(f"[{r['category']}] {r['label']}\n")
            f.write(f"    text                : {r['text']}\n")
            f.write(f"    characters          : {r['n_chars']}\n")
            f.write(f"    bytes (= regions)   : {r['n_bytes']}\n")
            f.write(f"    bytes / character   : {r['bytes_per_char']:.3f}\n")
            f.write(f"    unique regions      : {r['unique_regions']}\n")
            f.write(f"    region entropy bits : {r['region_entropy_bits']:.3f}\n")
            f.write(f"    bridge regions      : {r['bridges']}\n")
            f.write(f"    unreachable (proxy) : {r['unreachable']}\n")
            f.write(f"    regions traversed   : {r['regions_traversed']}\n")
            f.write(f"    amplification/char  : {r['amplification_per_char']:.3f}\n\n")

        f.write("Pairwise genome divergence (Levenshtein over region sequences)\n")
        f.write("-" * 60 + "\n")
        labels = [records[k]["category"][:10] for k in ORDER]
        f.write("            " + " ".join(f"{l:>10}" for l in labels) + "\n")
        for i, k in enumerate(ORDER):
            row = " ".join(f"{div[i, j]:10.0f}" for j in range(len(ORDER)))
            f.write(f"{labels[i]:>10}  {row}\n")
        # mean off-diagonal divergence
        n = len(ORDER)
        off = [div[i, j] for i in range(n) for j in range(n) if i != j]
        f.write(f"\nMean pairwise genome divergence: {np.mean(off):.2f}\n")
    print(f"Saved {out}")

    # also dump JSON for programmatic reuse / the website
    jout = os.path.join("results", "metrics", "case_studies.json")
    with open(jout, "w", encoding="utf-8") as f:
        json.dump({k: {kk: vv for kk, vv in records[k].items()} for k in ORDER},
                  f, ensure_ascii=False, indent=2)
    print(f"Saved {jout}")


def run_part_4():
    print("Running Part 4: Artistic Case Studies (Structural Amplification)")
    records, div = analyze()

    # console summary
    print("\n=== Structural Amplification Summary ===")
    for k in ORDER:
        r = records[k]
        print(f"  {r['category']:18s} chars={r['n_chars']:3d} bytes={r['n_bytes']:3d} "
              f"bridges={r['bridges']:3d} traversed={r['regions_traversed']:3d} "
              f"amp/char={r['amplification_per_char']:.2f} "
              f"entropy={r['region_entropy_bits']:.2f}")
    n = len(ORDER)
    off = [div[i, j] for i in range(n) for j in range(n) if i != j]
    print(f"\n  Mean pairwise genome divergence: {np.mean(off):.2f}")

    plot_genome(records)
    plot_amplification(records)
    write_metrics(records, div)


# =========================================================================== #
#  Part 5: Rendered Choreography Montages
# --------------------------------------------------------------------------- #
#  Render the physicalized choreography produced by the case-study texts, so the
#  embodied dance can be shown as renders (not UI plots). Three figures:
#    - plot_8_teaser.png       : one expressive keyframe for each of the seven
#                                case-study texts, side by side.
#    - plot_7_dance_montage.png: time-sampled keyframe strips for a contrasting
#                                trio (a sonnet, an error log, an Indigenous
#                                script), each shown as a sequence over time.
#    - plot_9_trail.png        : a chronophotographic long-exposure sweep of one
#                                dance across time.
#
#  All motion is generated by the same deterministic engine; nothing here is
#  posed by hand. Uses pyrender, so it takes a few minutes.
# =========================================================================== #

# key -> (register, readable sub-label, short teaser label, raw input text).
# Mirrors CASE_STUDIES above so figures and metrics agree.
CORPUS = {
    "canon":        ("Literary canon",    "Shakespeare, Sonnet 18", "Sonnet",
                     "Shall I compare thee to a summer's day?"),
    "marginalized": ("Marginalized voice", "Sojourner Truth, 1851", "Sojourner Truth",
                     "Ain't I a woman?"),
    "devanagari":   ("Non-Latin script",  "Hindi / Devanagari", "Devanagari",
                     "मैं नाचता हूँ"),
    "cherokee":     ("Indigenous script", "Cherokee syllabary", "Cherokee",
                     "ᏣᎳᎩ ᎦᏬᏂᎯᏍᏗ"),
    "code":         ("Source code",       "A line of Python", "Python",
                     "for i in range(256): codebook[i] = kmeans.predict(x)"),
    "machine":      ("Machine exhaust",   "Python traceback", "Traceback",
                     'Traceback (most recent call last): File "app.py", line 42, in <module>'),
    "signal":       ("Signal vs. noise",  "SOS, in Morse", "SOS",
                     "... --- ..."),
}

TEASER_ORDER = ["canon", "marginalized", "devanagari", "cherokee", "code", "machine", "signal"]
MONTAGE_KEYS = ["canon", "machine", "cherokee"]  # a deliberately contrasting trio

N_KEYS = 6                      # keyframes per row in the montage
VIEW_W, VIEW_H = 420, 540
CHAR_COLOR = [0.5, 0.2, 0.8, 1.0]  # neutral purple


def build_scene(grid=True):
    scene = pyrender.Scene(ambient_light=(0.6, 0.6, 0.6), bg_color=[1.0, 1.0, 1.0, 1.0])
    camera = pyrender.PerspectiveCamera(yfov=np.pi / 3.0)

    key_light = pyrender.DirectionalLight(color=[1.0, 0.95, 0.9], intensity=2.5)
    kl = np.eye(4); kl[:3, :3] = tra.euler_matrix(np.radians(-45), np.radians(45), 0)[:3, :3]
    scene.add(key_light, pose=kl)
    fill_light = pyrender.DirectionalLight(color=[0.9, 0.95, 1.0], intensity=1.2)
    fl = np.eye(4); fl[:3, :3] = tra.euler_matrix(np.radians(-30), np.radians(-45), 0)[:3, :3]
    scene.add(fill_light, pose=fl)
    back_light = pyrender.DirectionalLight(color=[1.0, 1.0, 1.0], intensity=2.0)
    bl = np.eye(4); bl[:3, :3] = tra.euler_matrix(np.radians(-135), 0, 0)[:3, :3]
    scene.add(back_light, pose=bl)

    if grid:
        # floor + grid for spatial grounding (used in the detailed montage)
        floor = trimesh.creation.box(extents=[40.0, 0.02, 40.0]); floor.apply_translation([0, -0.01, 0])
        floor_mat = pyrender.MetallicRoughnessMaterial(baseColorFactor=[0.96, 0.96, 0.96, 1.0],
                                                       metallicFactor=0.1, roughnessFactor=0.85)
        scene.add(pyrender.Mesh.from_trimesh(floor, material=floor_mat, smooth=False))
        cyls = []
        for x in np.arange(-6, 7, 1):
            c = trimesh.creation.cylinder(radius=0.005, height=12.0); c.apply_translation([x, 0.01, 0]); cyls.append(c)
        for z in np.arange(-6, 7, 1):
            c = trimesh.creation.cylinder(radius=0.005, height=12.0)
            c.apply_transform(tra.rotation_matrix(np.pi / 2, [0, 1, 0])); c.apply_translation([0, 0.01, z]); cyls.append(c)
        gridmesh = trimesh.util.concatenate(cyls)
        grid_mat = pyrender.MetallicRoughnessMaterial(baseColorFactor=[0.7, 0.7, 0.7, 1.0],
                                                      metallicFactor=0.0, roughnessFactor=1.0)
        scene.add(pyrender.Mesh.from_trimesh(gridmesh, material=grid_mat, smooth=False))

    cam_pose = np.eye(4) @ tra.rotation_matrix(np.radians(-12), [1, 0, 0])
    cam_pose[1, 3] = 0.9
    cam_pose[2, 3] = 3.0
    scene.add(camera, pose=cam_pose)
    return scene


def render_keyframes(poses, trans, indices, body_model, color, grid=True):
    scene = build_scene(grid=grid)
    renderer = pyrender.OffscreenRenderer(viewport_width=VIEW_W, viewport_height=VIEW_H)
    mat = pyrender.MetallicRoughnessMaterial(baseColorFactor=color, metallicFactor=0.2,
                                             roughnessFactor=0.6, doubleSided=True)
    imgs = []
    for idx in indices:
        p = torch.tensor(np.asarray(poses[idx:idx + 1]), dtype=torch.float32)
        y = float(np.asarray(trans[idx])[1])
        transl = torch.tensor([[0.0, y, 0.0]], dtype=torch.float32)  # center horizontally
        out = body_model(global_orient=p[:, :3], body_pose=p[:, 3:], transl=transl)
        verts = out.vertices.detach().cpu().numpy().squeeze()
        mesh = trimesh.Trimesh(verts, body_model.faces)
        node = scene.add(pyrender.Mesh.from_trimesh(mesh, material=mat, smooth=True))
        color_img, _ = renderer.render(scene, flags=pyrender.RenderFlags.RGBA)
        scene.remove_node(node)
        imgs.append(color_img[..., :3])
    renderer.delete()
    return imgs


def pick_expressive_frame(poses, trans, body_model):
    """Choose the most 'open' pose (limbs farthest from the pelvis) from the
    middle of the sequence, so each teaser body reads as a dynamic silhouette."""
    n = len(poses)
    lo, hi = int(n * 0.15), int(n * 0.90)
    cands = np.linspace(lo, max(lo + 1, hi), 8).astype(int)
    best, best_spread = int(cands[len(cands) // 2]), -1.0
    try:
        for idx in cands:
            p = torch.tensor(np.asarray(poses[idx:idx + 1]), dtype=torch.float32)
            out = body_model(global_orient=p[:, :3], body_pose=p[:, 3:],
                             transl=torch.zeros((1, 3), dtype=torch.float32))
            j = out.joints.detach().cpu().numpy().squeeze()
            spread = float(np.linalg.norm(j - j[0:1], axis=1).sum())
            if spread > best_spread:
                best_spread, best = spread, int(idx)
    except Exception as e:
        print(f"  (expressive-frame fallback: {e})")
    return best


def render_teaser(motions, body_model):
    order = TEASER_ORDER
    fig, axes = plt.subplots(1, len(order), figsize=(len(order) * 1.7, 2.7))
    for ax, key in zip(axes, order):
        register, sublabel, tlabel, poses, trans = motions[key]
        idx = pick_expressive_frame(poses, trans, body_model)
        img = render_keyframes(poses, trans, [idx], body_model, CHAR_COLOR, grid=False)[0]
        ax.imshow(img)
        ax.set_xticks([]); ax.set_yticks([])
        for s in ax.spines.values():
            s.set_visible(False)
        ax.set_xlabel(tlabel, fontsize=9.5)
    plt.tight_layout()
    out = "results/plots/plot_8_teaser.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"Saved {out}")


def render_montage(motions, body_model):
    keys = MONTAGE_KEYS
    fig, axes = plt.subplots(len(keys), N_KEYS, figsize=(N_KEYS * 1.85, len(keys) * 2.55))
    for r, key in enumerate(keys):
        register, sublabel, tlabel, poses, trans = motions[key]
        n = len(poses)
        lo, hi = int(n * 0.06), int(n * 0.94)
        indices = np.linspace(lo, max(lo + 1, hi), N_KEYS).astype(int)
        imgs = render_keyframes(poses, trans, indices, body_model, CHAR_COLOR, grid=True)
        for c in range(N_KEYS):
            ax = axes[r, c]
            ax.imshow(imgs[c]); ax.set_xticks([]); ax.set_yticks([])
            for s in ax.spines.values():
                s.set_visible(False)
            if c == 0:
                ax.set_ylabel(register, fontsize=11)
        axes[r, 0].text(0.0, -0.13, sublabel, transform=axes[r, 0].transAxes,
                        fontsize=8.5, style="italic", color="#444")
    plt.tight_layout()
    out = "results/plots/plot_7_dance_montage.png"
    fig.savefig(out, dpi=170, bbox_inches="tight")
    plt.close()
    print(f"Saved {out}")


def render_trail(motions, body_model, key, out_name):
    """A chronophotographic 'motion study': sample one dance across time, spread
    the frames left to right, color them by moment, and composite them into a
    single long-exposure sweep. The whole image is produced from the byte
    structure of one text."""
    register, sublabel, tlabel, poses, trans = motions[key]
    n = len(poses)
    n_frames = 14
    lo, hi = int(n * 0.08), int(n * 0.92)
    idxs = np.linspace(lo, max(lo + 1, hi), n_frames).astype(int)
    spread = 3.8
    xs = np.linspace(-spread / 2.0, spread / 2.0, n_frames)
    W, H = 1800, 640

    scene = pyrender.Scene(ambient_light=(0.6, 0.6, 0.6), bg_color=[1.0, 1.0, 1.0, 0.0])
    key_light = pyrender.DirectionalLight(color=[1.0, 0.95, 0.9], intensity=2.5)
    kl = np.eye(4); kl[:3, :3] = tra.euler_matrix(np.radians(-45), np.radians(45), 0)[:3, :3]
    scene.add(key_light, pose=kl)
    fill_light = pyrender.DirectionalLight(color=[0.9, 0.95, 1.0], intensity=1.2)
    fl = np.eye(4); fl[:3, :3] = tra.euler_matrix(np.radians(-30), np.radians(-45), 0)[:3, :3]
    scene.add(fill_light, pose=fl)
    back_light = pyrender.DirectionalLight(color=[1.0, 1.0, 1.0], intensity=2.0)
    bl = np.eye(4); bl[:3, :3] = tra.euler_matrix(np.radians(-135), 0, 0)[:3, :3]
    scene.add(back_light, pose=bl)
    camera = pyrender.PerspectiveCamera(yfov=np.pi / 3.0)
    cam_pose = np.eye(4) @ tra.rotation_matrix(np.radians(-10), [1, 0, 0])
    cam_pose[1, 3] = 0.9
    cam_pose[2, 3] = 3.3
    scene.add(camera, pose=cam_pose)

    renderer = pyrender.OffscreenRenderer(viewport_width=W, viewport_height=H)
    cmap = plt.get_cmap("turbo")
    canvas = np.ones((H, W, 3), dtype=float)
    for i, idx in enumerate(idxs):
        col = cmap(0.08 + 0.84 * i / (n_frames - 1))
        mat = pyrender.MetallicRoughnessMaterial(
            baseColorFactor=[col[0], col[1], col[2], 1.0],
            metallicFactor=0.2, roughnessFactor=0.6, doubleSided=True)
        p = torch.tensor(np.asarray(poses[idx:idx + 1]), dtype=torch.float32)
        y = float(np.asarray(trans[idx])[1])
        transl = torch.tensor([[float(xs[i]), y, 0.0]], dtype=torch.float32)
        out = body_model(global_orient=p[:, :3], body_pose=p[:, 3:], transl=transl)
        verts = out.vertices.detach().cpu().numpy().squeeze()
        mesh = trimesh.Trimesh(verts, body_model.faces)
        node = scene.add(pyrender.Mesh.from_trimesh(mesh, material=mat, smooth=True))
        rgba, _ = renderer.render(scene, flags=pyrender.RenderFlags.RGBA)
        scene.remove_node(node)
        rgb = rgba[..., :3].astype(float) / 255.0
        alpha = (rgba[..., 3].astype(float) / 255.0)[..., None]
        weight = 0.30 + 0.70 * (i / (n_frames - 1))
        alpha = alpha * weight
        canvas = canvas * (1.0 - alpha) + rgb * alpha
    renderer.delete()

    canvas = np.clip(canvas, 0.0, 1.0)
    # crop away surrounding whitespace for a tight frame
    mask = (canvas < 0.98).any(axis=2)
    rows = np.where(mask.any(axis=1))[0]
    cols = np.where(mask.any(axis=0))[0]
    if len(rows) and len(cols):
        pad = 25
        r0, r1 = max(0, rows[0] - pad), min(canvas.shape[0], rows[-1] + pad)
        c0, c1 = max(0, cols[0] - pad), min(canvas.shape[1], cols[-1] + pad)
        canvas = canvas[r0:r1, c0:c1]
    fig = plt.figure(figsize=(canvas.shape[1] / 220.0, canvas.shape[0] / 220.0))
    ax = fig.add_axes([0, 0, 1, 1]); ax.imshow(canvas); ax.axis("off")
    fig.savefig(f"results/plots/{out_name}", dpi=220)
    plt.close()
    print(f"Saved results/plots/{out_name}")


def run_part_5():
    print("Running Part 5: Rendered Choreography Montages")
    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
    np.random.seed(7)
    body_model = smplx.create("models", model_type="smpl", gender="neutral", batch_size=1)

    # Generate the choreography for every case-study text once, then reuse it for
    # both the teaser (breadth: 7 texts) and the montage (depth: 3 texts over time).
    motions = {}
    for key in TEASER_ORDER:
        register, sublabel, tlabel, text = CORPUS[key]
        print(f"Generating choreography for: {register} — {sublabel}")
        _, poses, trans = generate_motion(0, f"fig_{key}", input_text=text,
                                          gender="neutral", physics_algorithms_on=True,
                                          render_video=False, verbose=False)
        print(f"  frames={len(poses)}")
        motions[key] = (register, sublabel, tlabel, poses, trans)

    render_teaser(motions, body_model)
    render_montage(motions, body_model)
    render_trail(motions, body_model, "devanagari", "plot_9_trail.png")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--part', type=int, choices=[1, 2, 3, 4, 5], help="Run a specific part of the analysis (1, 2, 3, 4, or 5).")
    args = parser.parse_args()
    
    np.random.seed(42)
    random.seed(42)
    torch.manual_seed(42)
    
    ensure_dirs()
    
    if args.part == 1 or args.part is None:
        run_part_1()
    
    if args.part == 2 or args.part is None:
        run_part_2()
        
    if args.part == 3 or args.part is None:
        run_part_3()

    if args.part == 4 or args.part is None:
        run_part_4()

    if args.part == 5 or args.part is None:
        run_part_5()

if __name__ == "__main__":
    main()
