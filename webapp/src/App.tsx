import React from 'react';
import {
  Box, Typography, Button, Container, Divider, Chip,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper,
  AppBar, Toolbar, ThemeProvider, createTheme,
} from '@mui/material';
import GitHubIcon from '@mui/icons-material/GitHub';
import { MathJaxContext, MathJax } from 'better-react-mathjax';

const GITHUB_URL = 'https://github.com/ML72/Text-In-Motion';

// A light, consistent theme so buttons and headings feel intentional rather
// than styled ad hoc at each call site.
const theme = createTheme({
  palette: {
    primary: { main: '#1976d2' },
    secondary: { main: '#9c27b0' },
    text: { primary: '#0f172a', secondary: '#475569' },
  },
  typography: {
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
    h3: { fontWeight: 700, letterSpacing: '-0.02em' },
    h4: { fontWeight: 700, letterSpacing: '-0.015em' },
    h5: { fontWeight: 600 },
    h6: { fontWeight: 600 },
    button: { textTransform: 'none', fontWeight: 600 },
  },
  shape: { borderRadius: 10 },
});

// --- Small presentational helpers ------------------------------------------

const Figure: React.FC<{ src: string; alt: string; caption: React.ReactNode }> = ({ src, alt, caption }) => (
  <Box sx={{ mt: 3, mb: 2, textAlign: 'center' }}>
    <img src={src} alt={alt} style={{ width: '100%', height: 'auto', borderRadius: '10px', border: '1px solid rgba(0,0,0,0.06)' }} />
    <Typography variant='caption' sx={{ display: 'block', mt: 1.5, mx: 'auto', maxWidth: 760, color: 'text.secondary', fontStyle: 'italic', lineHeight: 1.6 }}>
      {caption}
    </Typography>
  </Box>
);

const MetricCard: React.FC<{ value: string; label: string; sub: React.ReactNode }> = ({ value, label, sub }) => (
  <Box sx={{ p: 3, borderRadius: 2, border: '1px solid rgba(0,0,0,0.08)', background: '#ffffff', height: '100%' }}>
    <Typography sx={{ fontWeight: 700, fontSize: '1.9rem', lineHeight: 1.1, background: '-webkit-linear-gradient(45deg, #1976d2, #9c27b0)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
      {value}
    </Typography>
    <Typography variant='subtitle2' sx={{ fontWeight: 700, mt: 1 }}>{label}</Typography>
    <Typography variant='body2' sx={{ color: 'text.secondary', mt: 0.5, lineHeight: 1.6 }}>{sub}</Typography>
  </Box>
);

// --- Case-study corpus (metrics from the paper / results/metrics) -----------

const CASES = [
  { register: 'Sonnet (canon)',       label: 'Shakespeare, Sonnet 18',  chars: 39, regions: 41, amp: 1.05, entropy: 3.94, amplified: false },
  { register: 'Sojourner Truth',      label: 'Marginalized voice, 1851', chars: 16, regions: 16, amp: 1.00, entropy: 3.45, amplified: false },
  { register: 'Hindi / Devanagari',   label: 'Non-Latin script',         chars: 13, regions: 38, amp: 2.92, entropy: 2.86, amplified: true },
  { register: 'Cherokee',             label: 'Indigenous syllabary',     chars: 10, regions: 40, amp: 4.00, entropy: 3.09, amplified: true },
  { register: 'Source code (Python)', label: 'A line of Python',         chars: 52, regions: 67, amp: 1.29, entropy: 4.53, amplified: false },
  { register: 'Traceback (machine)',  label: 'Python error log',         chars: 70, regions: 75, amp: 1.07, entropy: 4.49, amplified: false },
  { register: 'SOS / Morse',          label: 'Signal vs. noise',         chars: 11, regions: 12, amp: 1.09, entropy: 1.44, amplified: false },
];

const KEYWORDS = ['Amplification', 'Embodied visualization', 'Data physicalization', 'Generative art', 'Motion synthesis'];

const App: React.FC = () => {
  return (
    <ThemeProvider theme={theme}>
    <MathJaxContext>

      {/* Top navigation bar */}
      <AppBar
        position='sticky'
        elevation={0}
        sx={{ background: 'rgba(255,255,255,0.82)', backdropFilter: 'blur(10px)', borderBottom: '1px solid rgba(0,0,0,0.08)', color: 'text.primary' }}
      >
        <Container maxWidth='md'>
          <Toolbar disableGutters sx={{ minHeight: 60, gap: 2 }}>
            <Typography variant='subtitle1' sx={{ fontWeight: 700, flexGrow: 1, letterSpacing: '-0.01em' }}>
              The Choreographic Genome
            </Typography>
            <Button
              size='small'
              variant='outlined'
              startIcon={<GitHubIcon />}
              href={GITHUB_URL}
              target='_blank'
              rel='noopener'
              sx={{ borderColor: 'rgba(0,0,0,0.18)', color: 'text.primary', '&:hover': { borderColor: 'primary.main', backgroundColor: 'rgba(25,118,210,0.04)' } }}
            >
              Code
            </Button>
          </Toolbar>
        </Container>
      </AppBar>

      <Box sx={{ minHeight: '100vh', background: 'radial-gradient(circle at 50% 0%, #ffffff 0%, #f0f4f8 100%)', color: 'text.primary', pt: { xs: 5, md: 7 }, pb: 10 }}>
        <Container maxWidth='md'>

          {/* Header Section */}
          <Box sx={{ textAlign: 'center', mb: 4 }}>
            <Typography variant='h4' component='h1' gutterBottom sx={{ background: '-webkit-linear-gradient(45deg, #1976d2, #9c27b0)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              The Choreographic Genome: Amplifying the Silent Structure of Text into Dance
            </Typography>
            <Typography variant='subtitle1' sx={{ color: 'text.secondary', mt: 2 }}>
              Michael Li and Alison Ding, Carnegie Mellon University
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: 1, mt: 2.5 }}>
              {KEYWORDS.map((k) => (
                <Chip key={k} label={k} size='small' variant='outlined' sx={{ borderColor: 'rgba(0,0,0,0.12)', color: 'text.secondary' }} />
              ))}
            </Box>
          </Box>

          {/* Teaser hero */}
          <Figure
            src='plot_8_teaser.png'
            alt='One expressive keyframe of the dance generated for each of seven case-study texts.'
            caption={<>
              <strong>Seven texts, seven bodies.</strong> A single expressive keyframe from the choreography our
              instrument generates for each case-study text, from a Shakespeare sonnet to an &ldquo;SOS&rdquo; in Morse.
              The mapping from text to movement never consults meaning, only structure, yet each text still produces a
              visibly distinct dance. Every body is rendered from the same underlying engine.
            </>}
          />

          <Divider sx={{ borderColor: 'rgba(0,0,0,0.08)', my: 6 }} />

          {/* Abstract Section */}
          <Box sx={{ mb: 6 }}>
            <Typography variant='h4' component='h2' gutterBottom>
              Abstract
            </Typography>
            <Typography variant='body1' sx={{ color: 'text.secondary', lineHeight: 1.8 }}>
              Recent advances in generative artificial intelligence have enabled the synthesis of complex human motion
              with unprecedented fidelity. However, current text-to-motion systems rely strictly on linguistic semantics:
              if an input reads &ldquo;I put my hands up,&rdquo; the model searches for a pose with raised hands, and every
              non-semantic property of the text is discarded as noise. In this work, we treat that discarded structure as
              the signal. We present an embodied visualization instrument that amplifies not what a text means, but how it
              is built. Our method first quantizes dance kinematics into a motion codebook of 256 stylistic &ldquo;regions&rdquo;
              using Principal Component Analysis and K-Means clustering. We then map the raw byte representation of any input
              text directly onto this codebook, producing a deterministic sequence of regions that we call the text&rsquo;s
              &ldquo;choreographic genome.&rdquo; A precomputed plausibility graph and a set of physics smoothing routines
              turn this genome into fluid, full-body movement, so that the dancing body becomes a display surface for the
              byte-level structure that semantic systems ignore. Through a series of artistic case studies (a Shakespeare
              sonnet, a machine error log, source code, an abolitionist&rsquo;s question, and Indigenous and Devanagari
              scripts), we show that each text produces a visibly distinct dance, and that scripts marginalized by
              ASCII-centric computing are amplified into three to four times more movement per character. We frame this not
              as a motion-synthesis benchmark, but as a critical and poetic visualization that asks what we choose to count
              as signal, and what we allow to go unheard.
            </Typography>
          </Box>

          <Divider sx={{ borderColor: 'rgba(0,0,0,0.08)', mb: 6 }} />

          {/* The Inversion (motivation) */}
          <Box sx={{ mb: 6 }}>
            <Typography variant='h4' component='h2' gutterBottom>
              The Inversion
            </Typography>
            <Typography variant='body1' sx={{ color: 'text.secondary', lineHeight: 1.8 }}>
              Data surrounds us, but not all of it is heard equally. Some signals become visible, operative, and powerful,
              while others remain quiet, fragmented, or deliberately ignored. Visualization can be an instrument of
              amplification, a way to make the quiet legible and the overlooked present. We take that idea literally, and
              ask a pointed question about our own instruments: when we build a system to turn up a signal, what does it
              make louder, and what does it silence?
              <br /><br />
              Text is one of the most quietly structured data streams we produce. Every message carries far more than its
              dictionary meaning: an encoding, a distribution of bytes, a choice of script, a rhythm of repetition. Yet the
              dominant paradigm of generative AI is built to hear only one of these layers. Text-to-motion and
              text-to-image models treat semantic content as literal instruction and discard everything else as noise. If
              the lyrics say &ldquo;I put my hands up,&rdquo; the model returns a figure with raised hands, and the
              structure of the language, its actual material, is silenced in favor of its most sanctioned reading.
              <br /><br />
              Our instrument inverts this hierarchy. Rather than amplifying what a text <em>means</em>, we amplify how it is
              <em> built</em>. Because the mapping never consults meaning, every text, whether a sonnet, an error log, a
              protest, a line of code, or a script that ASCII never planned for, is given a body on equal terms.
            </Typography>
          </Box>

          <Divider sx={{ borderColor: 'rgba(0,0,0,0.08)', mb: 6 }} />

          {/* The Choreographic Genome (core concept) */}
          <Box sx={{ mb: 6 }}>
            <Typography variant='h4' component='h2' gutterBottom>
              The Choreographic Genome
            </Typography>
            <Typography variant='body1' sx={{ color: 'text.secondary', lineHeight: 1.8 }}>
              The core of the system is intentionally, almost provocatively, simple. Let a text be its UTF-8 byte sequence
              <MathJax inline>{" \\(b_1 b_2 \\cdots b_n\\) "}</MathJax>, where each byte lies in
              <MathJax inline>{" \\([0, 255]\\)"}</MathJax>. The choreographic genome is the identity map from bytes to
              motion regions:
            </Typography>
            <Box sx={{ my: 3, p: 3, borderRadius: 2, border: '1px solid rgba(0,0,0,0.08)', background: 'rgba(25,118,210,0.04)', textAlign: 'center', overflowX: 'auto' }}>
              <MathJax>{"\\[ \\Phi(b_1 b_2 \\cdots b_n) = r_1 r_2 \\cdots r_n, \\qquad r_i = b_i \\]"}</MathJax>
            </Box>
            <Typography variant='body1' sx={{ color: 'text.secondary', lineHeight: 1.8 }}>
              There is no learning in this step, no inference of intent, and no semantic lookup, and that is precisely the
              point: the map amplifies structure because it refuses to interpret. Two texts that mean the same thing but are
              built differently produce different genomes. Furthermore, a text written in a multibyte script produces a
              longer genome than its character count would suggest, because the encoding itself is part of the signal we
              have chosen to hear.
            </Typography>
            <Figure
              src='plot_5_choreographic_genome.png'
              alt='Choreographic genome strips: each text rendered as a colored sequence of motion-region ids.'
              caption={<>
                The <strong>choreographic genome</strong>. Each text is amplified, byte by byte, into a sequence of motion
                regions, where color encodes region id. Because UTF-8 spends more bytes on non-Latin scripts, the Devanagari
                and Cherokee strips run long and warm despite their short character counts, while the &ldquo;SOS&rdquo;
                distress call collapses into a brief, repetitive pulse. Each text yields a visibly distinct genome, with a
                mean pairwise edit distance of 44.3 across the corpus.
              </>}
            />
          </Box>

          <Divider sx={{ borderColor: 'rgba(0,0,0,0.08)', mb: 6 }} />

          {/* Case Studies */}
          <Box sx={{ mb: 6 }}>
            <Typography variant='h4' component='h2' gutterBottom>
              Amplifying Texts: Case Studies
            </Typography>
            <Typography variant='body1' sx={{ color: 'text.secondary', lineHeight: 1.8, mb: 1 }}>
              To study the instrument as a visualization rather than as a benchmark, we assembled a deliberately
              heterogeneous corpus: the loud Western canon, the overlooked exhaust of machines, historically marginalized
              voices, and scripts that digital infrastructure was never centered on. For each text we compute its genome and
              measure the movement required to physically realize it.
            </Typography>

            <TableContainer component={Paper} elevation={0} sx={{ border: '1px solid rgba(0,0,0,0.08)', mt: 3, mb: 1 }}>
              <Table size='small'>
                <TableHead>
                  <TableRow sx={{ '& th': { fontWeight: 700 } }}>
                    <TableCell>Text (register)</TableCell>
                    <TableCell align='right'>Chars</TableCell>
                    <TableCell align='right'>Regions</TableCell>
                    <TableCell align='right'>Amp./char</TableCell>
                    <TableCell align='right'>Entropy</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {CASES.map((c) => (
                    <TableRow key={c.register} sx={{ backgroundColor: c.amplified ? 'rgba(156,39,176,0.07)' : 'transparent' }}>
                      <TableCell>
                        <Typography variant='body2' sx={{ fontWeight: 600 }}>{c.register}</Typography>
                        <Typography variant='caption' sx={{ color: 'text.secondary' }}>{c.label}</Typography>
                      </TableCell>
                      <TableCell align='right'>{c.chars}</TableCell>
                      <TableCell align='right'>{c.regions}</TableCell>
                      <TableCell align='right' sx={{ fontWeight: c.amplified ? 700 : 400, color: c.amplified ? 'secondary.main' : 'inherit' }}>
                        {c.amp.toFixed(2)}
                      </TableCell>
                      <TableCell align='right'>{c.entropy.toFixed(2)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
            <Typography variant='caption' sx={{ display: 'block', color: 'text.secondary', fontStyle: 'italic', lineHeight: 1.6 }}>
              Structural amplification across the corpus. &ldquo;Regions&rdquo; counts the motion gestures the body
              traverses (bytes plus bridges inserted for physical continuity); &ldquo;amplification&rdquo; is regions per
              source character; &ldquo;entropy&rdquo; is over the region distribution. Highlighted rows are the multibyte
              scripts that UTF-8 encodes with several bytes per glyph.
            </Typography>

            {/* Every text has a body */}
            <Typography variant='h5' component='h3' sx={{ color: 'primary.main', mt: 5, mb: 1.5 }}>
              Every text has a body
            </Typography>
            <Typography variant='body1' sx={{ color: 'text.secondary', lineHeight: 1.8 }}>
              The genomes above are immediately and legibly different from one another, which confirms the instrument&rsquo;s
              basic claim: structure alone, with meaning withheld, is enough to give every text a distinct physical identity.
              Because the byte-to-region mapping is fully deterministic, the same text always yields the same genome, so this
              identity is stable and repeatable. The engine then realizes that genome through motion matching, and it is the
              genome, rather than any single performance, that serves as the text&rsquo;s fingerprint.
            </Typography>

            {/* Amplifying what ASCII marginalizes */}
            <Typography variant='h5' component='h3' sx={{ color: 'primary.main', mt: 5, mb: 1.5 }}>
              Amplifying what ASCII marginalizes
            </Typography>
            <Typography variant='body1' sx={{ color: 'text.secondary', lineHeight: 1.8 }}>
              The most pointed result is also the simplest. ASCII English spends roughly one byte per character, so the
              canonical and marginalized English texts amplify at about one region per character. However, UTF-8 spends two
              to four bytes on the scripts it treats as exceptions to a Latin default. The Devanagari phrase meaning &ldquo;I
              dance&rdquo; (13 characters) and a Cherokee phrase (10 characters) therefore unfold into 38 and 40 regions, at
              amplification factors of 2.9 and 4.0. The very encoding overhead that makes these scripts &ldquo;expensive&rdquo;
              and peripheral to computing becomes, in our instrument, a surplus of embodied expression: the overlooked script
              is given more body, not less.
            </Typography>
            <Figure
              src='plot_6_amplification.png'
              alt='Bar charts of motion regions traversed per character and region-distribution entropy per text.'
              caption={<>
                Left: motion regions traversed per character. Texts in scripts that UTF-8 encodes with several bytes per
                glyph are amplified into markedly more movement. Right: each text&rsquo;s region-distribution entropy, its
                structural signature. Source code and machine exhaust are the most varied, while the Morse distress call is
                the most repetitive.
              </>}
            />
            <Figure
              src='plot_9_trail.png'
              alt='A chronophotographic long-exposure sweep of a single generated dance.'
              caption={<>
                A chronophotographic view of a single generated dance. We sample one sequence across time, spread the frames
                left to right, and color them cool to warm by moment. The entire sweep is produced from the byte structure of
                the Devanagari phrase meaning &ldquo;I dance.&rdquo; The instrument never reads that meaning, yet the
                structure alone yields a complete choreographic arc.
              </>}
            />

            {/* Sonnet vs error log */}
            <Typography variant='h5' component='h3' sx={{ color: 'primary.main', mt: 5, mb: 1.5 }}>
              The dance of a sonnet versus an error log
            </Typography>
            <Typography variant='body1' sx={{ color: 'text.secondary', lineHeight: 1.8 }}>
              The same engine, given three different structures, choreographs three visibly different bodies. The sonnet,
              built from lowercase Latin letters that cluster in a narrow byte range, moves in relatively legato, recurring
              postures. The Python traceback, with its punctuation, digits, mixed case, and the bracketed debris of a crash,
              carries one of the highest structural entropies in the corpus (4.49 bits) and reads as jagged and percussive, a
              body stuttering through exception handling. The Cherokee syllabary, composed entirely of high continuation
              bytes, sweeps through the warm end of the codebook in long, dense phrases.
            </Typography>
            <Figure
              src='plot_7_dance_montage.png'
              alt='Time-sampled keyframe strips of the generated dance for three contrasting texts.'
              caption={<>
                Physicalized choreography: time-sampled keyframes from the same engine driven by three different texts. The
                sonnet (top) is comparatively legato, the machine traceback (middle) is percussive and high in entropy, and
                the Cherokee syllabary (bottom) moves through long, dense phrases. These are renders of the actual generated
                motion, not schematic illustrations.
              </>}
            />

            {/* What counts as signal */}
            <Typography variant='h5' component='h3' sx={{ color: 'primary.main', mt: 5, mb: 1.5 }}>
              What counts as signal
            </Typography>
            <Typography variant='body1' sx={{ color: 'text.secondary', lineHeight: 1.8 }}>
              The corpus also probes the central question directly. &ldquo;SOS&rdquo; in Morse is a message that is nothing
              but a call to be heard, and it holds almost no lexical content. Yet the instrument gives it the lowest-entropy
              genome in the set (1.44 bits): a short, insistent, repeating pulse. A semantic model would find nothing to say
              about three dots, three dashes, and three dots. Our structural amplifier instead produces a clear rhythmic
              signature, which raises the question of which of the two systems has actually registered the signal.
            </Typography>
          </Box>

          <Divider sx={{ borderColor: 'rgba(0,0,0,0.08)', mb: 6 }} />

          {/* How the Instrument Works */}
          <Box sx={{ mb: 6 }}>
            <Typography variant='h4' component='h2' gutterBottom>
              How the Instrument Works
            </Typography>
            <Typography variant='body1' sx={{ color: 'text.secondary', lineHeight: 1.8 }}>
              The pipeline shifts generation from a predictive neural paradigm to a classical, interpretable pathfinding
              approach. An offline phase quantizes continuous motion into a structural codebook and learns the physical rules
              for moving between its entries, and a runtime phase maps an input text onto that codebook and synthesizes the
              corresponding choreography. Every step is inspectable, so the instrument can explain itself rather than asking
              to be trusted.
            </Typography>

            <Box sx={{ mb: 4, mt: 3 }}>
              <Typography variant='h6' component='h3' gutterBottom sx={{ color: 'primary.main' }}>
                1. A vocabulary of movement
              </Typography>
              <Typography variant='body1' sx={{ color: 'text.secondary', lineHeight: 1.8 }}>
                We build the movement vocabulary from the AIST++ motion-capture corpus. Each pose is aligned to a local,
                translation- and heading-invariant frame, then described by its local joint configuration, its root and
                joint velocities, and binary foot-contact labels, for 278 features per frame. We window these over 20
                consecutive frames to produce a 5560-dimensional motion signature, reduce it to 64 dimensions with
                <strong> Principal Component Analysis</strong>, and quantize the result into 256 clusters with
                <strong> K-Means</strong>, exactly one cluster for each possible byte value. Each cluster, which we call a
                &ldquo;region,&rdquo; is a recurring stylistic gesture, and together the 256 regions form the codebook, the
                instrument&rsquo;s alphabet of the body.
              </Typography>
              <Box sx={{ mt: 3, mb: 2, textAlign: 'center' }}>
                <img src='codebook_grid.png' alt='Sample codebook regions' style={{ maxWidth: '100%', borderRadius: '10px', border: '1px solid rgba(0,0,0,0.06)' }} />
                <Typography variant='caption' sx={{ display: 'block', mt: 1.5, mx: 'auto', maxWidth: 760, color: 'text.secondary', fontStyle: 'italic', lineHeight: 1.6 }}>
                  Randomly sampled frames from each of the first 5 codebook regions. The patterns are not perfect, since the
                  quantization considers a window of motion rather than a single pose, and 256 regions cannot fully describe
                  the space of human movement, but frames drawn from the same region are qualitatively similar.
                </Typography>
              </Box>
            </Box>

            <Box sx={{ mb: 4 }}>
              <Typography variant='h6' component='h3' gutterBottom sx={{ color: 'primary.main' }}>
                2. Making the genome danceable
              </Typography>
              <Typography variant='body1' sx={{ color: 'text.secondary', lineHeight: 1.8 }}>
                Adjacent bytes routinely name gestures no human could perform back to back. Rather than smoothing this away
                invisibly, we treat physical continuity as an explicit, auditable layer. Offline, we precompute a directed
                &ldquo;plausibility graph&rdquo; over the 256 regions, using a motion-matching cost that compares pose, joint
                and root velocities, and the estimated root trajectory 15 and 30 frames into the future, with an extra
                penalty on root velocity to prevent abrupt momentum changes.
              </Typography>
              <Box sx={{ my: 2, overflowX: 'auto' }}>
                <MathJax>{"\\[C(x, x') = \\|p - p'\\|_2^2 + \\|\\dot{p} - \\dot{p}'\\|_2^2 + 10\\|\\dot{t} - \\dot{t}'\\|_2^2 + 2\\|\\Delta_{15} - \\Delta'_{15}\\|_2^2 + 2\\|\\Delta_{30} - \\Delta'_{30}\\|_2^2\\]"}</MathJax>
              </Box>
              <Typography variant='body1' sx={{ color: 'text.secondary', lineHeight: 1.8 }}>
                At runtime, when the genome demands a transition the body cannot make directly, we apply
                <strong> Dijkstra&rsquo;s algorithm</strong> over this graph to insert the shortest sequence of intermediate
                &ldquo;bridge&rdquo; regions, falling back to the nearest reachable region only when no path exists.
              </Typography>
            </Box>

            <Box sx={{ mb: 4 }}>
              <Typography variant='h6' component='h3' gutterBottom sx={{ color: 'primary.main' }}>
                3. Physics smoothing and correction
              </Typography>
              <Typography variant='body1' sx={{ color: 'text.secondary', lineHeight: 1.8 }}>
                Finally, we ease the disjoint segments together. Positional values are interpolated with a
                <strong> Perlin smootherstep</strong> polynomial for <MathJax inline>{"\\(C^2\\)"}</MathJax> continuous
                easing, joint rotations are blended with <strong>Spherical Linear Interpolation (SLERP)</strong> to avoid
                limb collapse, and a <strong>Savitzky-Golay filter</strong> together with an anti-skating correction removes
                residual jitter and foot sliding. The result honors the structure of the text while remaining
                biomechanically fluid.
              </Typography>
            </Box>
          </Box>

          <Divider sx={{ borderColor: 'rgba(0,0,0,0.08)', mb: 6 }} />

          {/* The Instrument in Motion (video demos) */}
          <Box sx={{ mb: 6 }}>
            <Typography variant='h4' component='h2' gutterBottom>
              The Instrument in Motion
            </Typography>
            <Typography variant='body1' sx={{ color: 'text.secondary', lineHeight: 1.8, mb: 1 }}>
              The figures above are keyframes; these are full renders of the engine in motion. Every clip is generated
              algorithmically by the pipeline described here, and no human posed the bodies.
            </Typography>

            {/* Autonomous Exploration */}
            <Box sx={{ mb: 6, mt: 3 }}>
              <Typography variant='h5' component='h3' gutterBottom sx={{ color: 'primary.main' }}>
                Autonomous Exploration
              </Typography>
              <Typography variant='body1' sx={{ color: 'text.secondary', lineHeight: 1.8, mb: 3 }}>
                With no textual input, the engine performs pure motion matching, sampling new sequences on the fly. It serves
                as a baseline that achieves high choreographic novelty but lacks the structural guidance of the text-driven
                approach, unfolding as an organically smooth, abstract flow.
              </Typography>
              <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' }, gap: 2 }}>
                <video src='videos/auto_male.mp4' autoPlay loop muted playsInline controls style={{ width: '100%', borderRadius: '10px' }} />
                <video src='videos/auto_female.mp4' autoPlay loop muted playsInline controls style={{ width: '100%', borderRadius: '10px' }} />
                <video src='videos/auto_neutral.mp4' autoPlay loop muted playsInline controls style={{ width: '100%', borderRadius: '10px' }} />
              </Box>
            </Box>

            {/* Text Guided Generation */}
            <Box sx={{ mb: 4 }}>
              <Typography variant='h5' component='h3' gutterBottom sx={{ color: 'primary.main' }}>
                Text-Guided Generation
              </Typography>
              <Typography variant='body1' sx={{ color: 'text.secondary', lineHeight: 1.8, mb: 4 }}>
                Here the raw bytes of the input text drive the genome directly, with Dijkstra bridging over the plausibility
                graph connecting biomechanically disconnected regions. The forced tempo changes give text-driven dances a
                distinct rhythmic, kinetic signature, unlike the homogeneous flow of the original dataset.
              </Typography>

              <Box sx={{ mb: 4 }}>
                <Typography variant='subtitle1' gutterBottom sx={{ fontWeight: 600 }}>
                  Guided by text &ldquo;i love you&rdquo;
                </Typography>
                <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' }, gap: 2 }}>
                  <video src='videos/text_ily_male.mp4' autoPlay loop muted playsInline controls style={{ width: '100%', borderRadius: '10px' }} />
                  <video src='videos/text_ily_female.mp4' autoPlay loop muted playsInline controls style={{ width: '100%', borderRadius: '10px' }} />
                  <video src='videos/text_ily_neutral.mp4' autoPlay loop muted playsInline controls style={{ width: '100%', borderRadius: '10px' }} />
                </Box>
              </Box>

              <Box sx={{ mb: 4 }}>
                <Typography variant='subtitle1' gutterBottom sx={{ fontWeight: 600 }}>
                  Guided by text &ldquo;Life begins where fear ends&rdquo;
                </Typography>
                <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' }, gap: 2 }}>
                  <video src='videos/text_lifebegins_male.mp4' autoPlay loop muted playsInline controls style={{ width: '100%', borderRadius: '10px' }} />
                  <video src='videos/text_lifebegins_female.mp4' autoPlay loop muted playsInline controls style={{ width: '100%', borderRadius: '10px' }} />
                  <video src='videos/text_lifebegins_neutral.mp4' autoPlay loop muted playsInline controls style={{ width: '100%', borderRadius: '10px' }} />
                </Box>
              </Box>

              <Box sx={{ mb: 2 }}>
                <Typography variant='subtitle1' gutterBottom sx={{ fontWeight: 600 }}>
                  Guided by text &ldquo;Your Midas touch on the Chevy door&rdquo;
                </Typography>
                <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' }, gap: 2 }}>
                  <video src='videos/text_midas_male.mp4' autoPlay loop muted playsInline controls style={{ width: '100%', borderRadius: '10px' }} />
                  <video src='videos/text_midas_female.mp4' autoPlay loop muted playsInline controls style={{ width: '100%', borderRadius: '10px' }} />
                  <video src='videos/text_midas_neutral.mp4' autoPlay loop muted playsInline controls style={{ width: '100%', borderRadius: '10px' }} />
                </Box>
              </Box>
            </Box>
          </Box>

          <Divider sx={{ borderColor: 'rgba(0,0,0,0.08)', mb: 6 }} />

          {/* Does the Instrument Work? (validation) */}
          <Box sx={{ mb: 6 }}>
            <Typography variant='h4' component='h2' gutterBottom>
              Does the Instrument Work?
            </Typography>
            <Typography variant='body1' sx={{ color: 'text.secondary', lineHeight: 1.8 }}>
              Amplification is only meaningful if the instrument is faithful and the body it drives is convincing. We do not
              position this as a more accurate motion model, and it should not be judged on motion-quality metrics alone, but
              a compact technical validation confirms that it is both inventive and physically credible.
            </Typography>
            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' }, gap: 2, mt: 3 }}>
              <MetricCard
                value='99.9%'
                label='Novel phrases'
                sub='of three-gram region transitions (and 100% of four-grams) are absent from the training corpus: the instrument composes rather than retrieves.'
              />
              <MetricCard
                value='0.43'
                label='Kinetic energy'
                sub='mean kinetic energy of text-driven motion versus 0.07 for training data; generated genomes also diverge sharply from one another (mean edit distance 32.5).'
              />
              <MetricCard
                value='0.59'
                label='Bridges / transition'
                sub='mean bridge regions Dijkstra inserts per transition; 54% of all region pairs are already connected directly, so most need none.'
              />
              <MetricCard
                value='12×'
                label='Less foot-skating'
                sub='the physics layer cuts foot-skating from 0.121 to 0.010 and jerk below the AIST++ baseline itself, with negligible floor penetration.'
              />
            </Box>
          </Box>

          <Divider sx={{ borderColor: 'rgba(0,0,0,0.08)', mb: 6 }} />

          {/* Discussion */}
          <Box sx={{ mb: 6 }}>
            <Typography variant='h4' component='h2' gutterBottom>
              Amplification Is Never Neutral
            </Typography>
            <Typography variant='body1' sx={{ color: 'text.secondary', lineHeight: 1.8 }}>
              The central contribution of this work is less the pipeline than the inversion it embodies. Semantic generation
              amplifies the part of language that is already loud, its sanctioned meaning, and in doing so reproduces the
              biases of whoever assembled the training data. By amplifying structure instead, our instrument turns up a
              signal present in every text but attended to in almost none, on equal terms for a sonnet and a stack trace.
              <br /><br />
              At the same time, we resist a triumphant reading of our own results. The movement vocabulary is learned from
              AIST++, a corpus of largely studio street dance, so the body that speaks every text is culturally specific, and
              the equal treatment we claim holds only with respect to that vocabulary. The amplification of multibyte scripts
              is a property of UTF-8, not evidence of any understanding of the languages it encodes; the instrument can give
              Cherokee more movement without knowing a single word of Cherokee. We consider this honesty to be part of the
              work.
              <br /><br />
              Because the core is classical and interpretable, an artist can actually read it: the genome is legible, the
              bridges are logged, and the same text reliably yields the same genome, which the engine can replay exactly when
              its random seed is fixed. This makes the system a partner to play and argue with rather than an oracle to be
              trusted. We imagine performers &ldquo;playing&rdquo; texts in real time, curators amplifying archival documents
              into embodied form, and communities choreographing words in scripts that mainstream models still render as empty
              boxes. In future work, we plan to broaden the codebook with more diverse kinetic datasets, such as classical
              ballet and everyday movement, to loosen this cultural specificity.
            </Typography>
          </Box>

          <Divider sx={{ borderColor: 'rgba(0,0,0,0.08)', mb: 4 }} />

          {/* Footer */}
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant='body2' sx={{ color: 'text.secondary', lineHeight: 1.8, mb: 2, mx: 'auto', maxWidth: 620 }}>
              Every figure on this page was generated by the system described here. The source code, motion codebook,
              plausibility graph, and case-study corpus are all publicly available.
            </Typography>
            <Button variant='contained' disableElevation startIcon={<GitHubIcon />} href={GITHUB_URL} target='_blank' rel='noopener' sx={{ px: 3 }}>
              View Code on GitHub
            </Button>
          </Box>

        </Container>
      </Box>
    </MathJaxContext>
    </ThemeProvider>
  );
};
export default App;
