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
  <Box sx={{ p: 3, borderRadius: 2, border: '1px solid rgba(0,0,0,0.08)', background: '#ffffff' }}>
    <Typography sx={{ fontWeight: 700, fontSize: '1.9rem', lineHeight: 1.1, background: '-webkit-linear-gradient(45deg, #1976d2, #9c27b0)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
      {value}
    </Typography>
    <Typography variant='subtitle2' sx={{ fontWeight: 700, mt: 1 }}>{label}</Typography>
    <Typography variant='body2' sx={{ color: 'text.secondary', mt: 0.5, lineHeight: 1.6 }}>{sub}</Typography>
  </Box>
);

// --- The case-study corpus (actual paper inputs + metrics from the paper) ---

type CaseItem = {
  register: string; label: string; text: string;
  chars: number; regions: number; amp: number; entropy: number; amplified: boolean;
};

const CASES: CaseItem[] = [
  { register: 'Sonnet', label: 'Literary canon', text: "Shall I compare thee to a summer's day?", chars: 39, regions: 41, amp: 1.05, entropy: 3.94, amplified: false },
  { register: 'Sojourner Truth', label: 'Marginalized voice', text: "Ain't I a woman?", chars: 16, regions: 16, amp: 1.00, entropy: 3.45, amplified: false },
  { register: 'Devanagari', label: 'Non-Latin script', text: 'मैं नाचता हूँ', chars: 13, regions: 38, amp: 2.92, entropy: 2.86, amplified: true },
  { register: 'Cherokee', label: 'Indigenous syllabary', text: 'ᏣᎳᎩ ᎦᏬᏂᎯᏍᏗ', chars: 10, regions: 40, amp: 4.00, entropy: 3.09, amplified: true },
  { register: 'Source code', label: 'A line of Python', text: 'for i in range(256): codebook[i] = kmeans.predict(x)', chars: 52, regions: 67, amp: 1.29, entropy: 4.53, amplified: false },
  { register: 'Traceback', label: 'Machine exhaust', text: 'Traceback (most recent call last): File "app.py", line 42, in <module>', chars: 70, regions: 75, amp: 1.07, entropy: 4.49, amplified: false },
  { register: 'SOS', label: 'Signal vs. noise, in Morse', text: '... --- ...', chars: 11, regions: 12, amp: 1.09, entropy: 1.44, amplified: false },
];

const STEPS = [
  { n: '1', title: 'A vocabulary of movement', body: 'We align AIST++ motion capture, extract 278 kinematic features per frame, window them over 20 frames, reduce to 64 dimensions with PCA, and cluster into 256 "regions" with K-Means, one per possible byte value.' },
  { n: '2', title: 'The genome', body: 'Each byte of the input maps straight to its region, the operator above, giving a deterministic choreographic score with no neural black box in the loop.' },
  { n: '3', title: 'Making it danceable', body: 'A plausibility graph inserts Dijkstra "bridge" regions between gestures no body could perform back to back, and Perlin, SLERP, and Savitzky-Golay smoothing yield fluid, plausible motion.' },
];

const KEYWORDS = ['Amplification', 'Embodied visualization', 'Data physicalization', 'Generative art', 'Motion synthesis'];

const videoStyle = { width: '100%', borderRadius: '10px' } as const;

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
              <strong>Seven texts, seven bodies.</strong> One keyframe from the dance our instrument generates for each
              case-study text, from a Shakespeare sonnet to an &ldquo;SOS&rdquo; in Morse. The mapping never consults
              meaning, only structure, yet each text produces a visibly distinct dance from the same underlying engine.
            </>}
          />

          <Divider sx={{ borderColor: 'rgba(0,0,0,0.08)', my: 6 }} />

          {/* Overview */}
          <Box sx={{ mb: 6 }}>
            <Typography variant='h4' component='h2' gutterBottom>
              Overview
            </Typography>
            <Typography variant='body1' sx={{ color: 'text.secondary', lineHeight: 1.8 }}>
              Current text-to-motion systems read only meaning: ask for &ldquo;hands up&rdquo; and you get raised hands,
              while every other property of the text is discarded as noise. We invert that. Our instrument amplifies not
              what a text means but how it is built, mapping the raw bytes of any string onto a learned vocabulary of 256
              motion &ldquo;regions&rdquo; to produce a deterministic dance we call its <em>choreographic genome</em>.
              Because the mapping never consults meaning, every text, whether a sonnet, an error log, or a script that ASCII
              never planned for, is given a body on equal terms. We offer this less as a better way to make dances than as a
              critical visualization that asks what we choose to count as signal, and what we let go unheard.
            </Typography>
          </Box>

          <Divider sx={{ borderColor: 'rgba(0,0,0,0.08)', mb: 6 }} />

          {/* The Choreographic Genome */}
          <Box sx={{ mb: 6 }}>
            <Typography variant='h4' component='h2' gutterBottom>
              The Choreographic Genome
            </Typography>
            <Typography variant='body1' sx={{ color: 'text.secondary', lineHeight: 1.8 }}>
              Let a text be its UTF-8 byte sequence <MathJax inline>{" \\(b_1 b_2 \\cdots b_n\\) "}</MathJax>, where each
              byte lies in <MathJax inline>{" \\([0, 255]\\)"}</MathJax>. The genome is simply the identity map from bytes
              to motion regions:
            </Typography>
            <Box sx={{ my: 3, p: 3, borderRadius: 2, border: '1px solid rgba(0,0,0,0.08)', background: 'rgba(25,118,210,0.04)', textAlign: 'center', overflowX: 'auto' }}>
              <MathJax>{"\\[ \\Phi(b_1 b_2 \\cdots b_n) = r_1 r_2 \\cdots r_n, \\qquad r_i = b_i \\]"}</MathJax>
            </Box>
            <Typography variant='body1' sx={{ color: 'text.secondary', lineHeight: 1.8 }}>
              There is no learning, no inference of intent, and no semantic lookup: the map amplifies structure precisely
              because it refuses to interpret. A multibyte script therefore produces a longer genome than its character
              count suggests, because the encoding itself is part of the signal we have chosen to hear.
            </Typography>
            <Figure
              src='plot_5_choreographic_genome.png'
              alt='Choreographic genome strips: each text rendered as a colored sequence of motion-region ids.'
              caption={<>
                Each text is amplified, byte by byte, into a sequence of motion regions (color encodes region id). UTF-8
                spends more bytes on non-Latin scripts, so the Devanagari and Cherokee strips run long and warm despite
                their short character counts, while &ldquo;SOS&rdquo; collapses into a brief, repetitive pulse.
              </>}
            />
          </Box>

          <Divider sx={{ borderColor: 'rgba(0,0,0,0.08)', mb: 6 }} />

          {/* The Corpus (examples) */}
          <Box sx={{ mb: 6 }}>
            <Typography variant='h4' component='h2' gutterBottom>
              The Corpus
            </Typography>
            <Typography variant='body1' sx={{ color: 'text.secondary', lineHeight: 1.8, mb: 1 }}>
              We ran a deliberately heterogeneous set of texts through the instrument: the Western canon, machine exhaust,
              marginalized voices, and scripts digital infrastructure was never centered on. Each row below is an actual
              input; every one yields a visibly distinct genome (mean pairwise edit distance 44.3 across the corpus).
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
                      <TableCell sx={{ maxWidth: 320 }}>
                        <Typography variant='body2' sx={{ fontWeight: 600 }}>
                          {c.register}
                          <Typography component='span' variant='caption' sx={{ color: 'text.secondary', fontWeight: 400, ml: 1 }}>{c.label}</Typography>
                        </Typography>
                        <Typography sx={{ fontFamily: 'source-code-pro, Menlo, Consolas, monospace', fontSize: 12, color: 'text.secondary', mt: 0.25, wordBreak: 'break-word' }}>
                          {c.text}
                        </Typography>
                      </TableCell>
                      <TableCell align='right'>{c.chars}</TableCell>
                      <TableCell align='right'>{c.regions}</TableCell>
                      <TableCell align='right' sx={{ fontWeight: c.amplified ? 700 : 400, color: c.amplified ? 'secondary.main' : 'inherit' }}>{c.amp.toFixed(2)}</TableCell>
                      <TableCell align='right'>{c.entropy.toFixed(2)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
            <Typography variant='caption' sx={{ display: 'block', color: 'text.secondary', fontStyle: 'italic', lineHeight: 1.6, mt: 1 }}>
              Structural amplification across the corpus. &ldquo;Regions&rdquo; counts the motion gestures the body
              traverses (bytes plus bridges inserted for physical continuity); &ldquo;amplification&rdquo; is regions per
              source character; &ldquo;entropy&rdquo; is over the region distribution. Highlighted rows are the multibyte
              scripts that UTF-8 encodes with several bytes per glyph.
            </Typography>

            <Typography variant='body1' sx={{ color: 'text.secondary', lineHeight: 1.8, mt: 4 }}>
              Because UTF-8 spends two to four bytes on non-Latin scripts, the Devanagari and Cherokee phrases unfold into
              roughly three to four times more movement per character: the encoding overhead that makes these scripts
              &ldquo;expensive&rdquo; and peripheral to computing becomes a surplus of embodied expression. At the other
              extreme, &ldquo;SOS&rdquo; in Morse collapses to the lowest-entropy genome in the set, a short, insistent
              pulse that a semantic model would find nothing to say about.
            </Typography>
            <Figure
              src='plot_6_amplification.png'
              alt='Bar charts of motion regions traversed per character and region-distribution entropy per text.'
              caption={<>
                Regions traversed per character (left) and each text&rsquo;s structural entropy (right). Scripts that UTF-8
                encodes with several bytes per glyph are amplified into markedly more movement; source code and machine
                exhaust are the most varied, the Morse call the most repetitive.
              </>}
            />
            <Figure
              src='plot_9_trail.png'
              alt='A chronophotographic long-exposure sweep of a single generated dance.'
              caption={<>
                One generated dance sampled across time and colored cool to warm by moment. The entire sweep is produced
                from the bytes of the Devanagari phrase meaning &ldquo;I dance,&rdquo; which the instrument never reads as
                meaning, yet the structure alone yields a complete choreographic arc.
              </>}
            />

            <Typography variant='body1' sx={{ color: 'text.secondary', lineHeight: 1.8, mt: 4 }}>
              Driven by three contrasting structures, the same engine choreographs three different bodies: a legato sonnet,
              a percussive traceback stuttering through its highest-entropy debris, and the long, warm phrases of Cherokee.
            </Typography>
            <Figure
              src='plot_7_dance_montage.png'
              alt='Time-sampled keyframe strips of the generated dance for three contrasting texts.'
              caption={<>
                Keyframes from the same engine driven by three texts: a legato sonnet (top), a percussive traceback
                (middle), and the long, dense phrases of Cherokee (bottom). These are renders of the actual generated
                motion, not schematic illustrations.
              </>}
            />
          </Box>

          <Divider sx={{ borderColor: 'rgba(0,0,0,0.08)', mb: 6 }} />

          {/* How It Works */}
          <Box sx={{ mb: 6 }}>
            <Typography variant='h4' component='h2' gutterBottom>
              How It Works
            </Typography>
            <Typography variant='body1' sx={{ color: 'text.secondary', lineHeight: 1.8 }}>
              The engine is classical and interpretable end to end, built on PCA, K-Means, and graph search rather than a
              black-box neural generator, and every step it takes is logged and inspectable.
            </Typography>
            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' }, gap: 2, mt: 3 }}>
              {STEPS.map((s) => (
                <Box key={s.n} sx={{ p: 3, borderRadius: 2, border: '1px solid rgba(0,0,0,0.08)', background: '#ffffff' }}>
                  <Box sx={{ width: 32, height: 32, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#ffffff', fontWeight: 700, background: 'linear-gradient(45deg, #1976d2, #9c27b0)', mb: 1.5 }}>
                    {s.n}
                  </Box>
                  <Typography variant='subtitle1' sx={{ fontWeight: 700, mb: 0.5 }}>{s.title}</Typography>
                  <Typography variant='body2' sx={{ color: 'text.secondary', lineHeight: 1.7 }}>{s.body}</Typography>
                </Box>
              ))}
            </Box>
          </Box>

          <Divider sx={{ borderColor: 'rgba(0,0,0,0.08)', mb: 6 }} />

          {/* The Instrument in Motion (video demos) */}
          <Box sx={{ mb: 6 }}>
            <Typography variant='h4' component='h2' gutterBottom>
              The Instrument in Motion
            </Typography>
            <Typography variant='body1' sx={{ color: 'text.secondary', lineHeight: 1.8, mb: 3 }}>
              The figures above are keyframes; these are full renders of the engine in motion, generated algorithmically
              and never posed by hand. The autonomous baseline explores the codebook freely, while text-guided runs are
              driven directly by the bytes of their input text.
            </Typography>

            <Typography variant='subtitle1' gutterBottom sx={{ fontWeight: 600 }}>
              Autonomous exploration (no text)
            </Typography>
            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' }, gap: 2, mb: 4 }}>
              <video src='videos/auto_male.mp4' autoPlay loop muted playsInline controls style={videoStyle} />
              <video src='videos/auto_female.mp4' autoPlay loop muted playsInline controls style={videoStyle} />
              <video src='videos/auto_neutral.mp4' autoPlay loop muted playsInline controls style={videoStyle} />
            </Box>

            <Typography variant='subtitle1' gutterBottom sx={{ fontWeight: 600 }}>
              Text-guided by &ldquo;i love you&rdquo;
            </Typography>
            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' }, gap: 2, mb: 4 }}>
              <video src='videos/text_ily_male.mp4' autoPlay loop muted playsInline controls style={videoStyle} />
              <video src='videos/text_ily_female.mp4' autoPlay loop muted playsInline controls style={videoStyle} />
              <video src='videos/text_ily_neutral.mp4' autoPlay loop muted playsInline controls style={videoStyle} />
            </Box>

            <Typography variant='subtitle1' gutterBottom sx={{ fontWeight: 600 }}>
              Text-guided by &ldquo;Your Midas touch on the Chevy door&rdquo;
            </Typography>
            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' }, gap: 2 }}>
              <video src='videos/text_midas_male.mp4' autoPlay loop muted playsInline controls style={videoStyle} />
              <video src='videos/text_midas_female.mp4' autoPlay loop muted playsInline controls style={videoStyle} />
              <video src='videos/text_midas_neutral.mp4' autoPlay loop muted playsInline controls style={videoStyle} />
            </Box>
          </Box>

          <Divider sx={{ borderColor: 'rgba(0,0,0,0.08)', mb: 6 }} />

          {/* Does the Instrument Work? (validation) */}
          <Box sx={{ mb: 6 }}>
            <Typography variant='h4' component='h2' gutterBottom>
              Does the Instrument Work?
            </Typography>
            <Typography variant='body1' sx={{ color: 'text.secondary', lineHeight: 1.8 }}>
              This is a critical visualization, not a benchmark, but a compact validation confirms the instrument is both
              inventive and physically credible.
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
                sub='mean kinetic energy of text-driven motion versus 0.07 for training data; generated genomes diverge sharply (mean edit distance 32.5).'
              />
              <MetricCard
                value='0.59'
                label='Bridges / transition'
                sub='mean bridge regions inserted per transition; 54% of all region pairs are already connected directly, so most need none.'
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
              We resist a triumphant reading of our own results. The vocabulary is learned from AIST++, a corpus of largely
              studio street dance, so the body that speaks every text is culturally specific, and the amplification of
              multibyte scripts is a property of UTF-8, not understanding: the instrument can give Cherokee more movement
              without knowing a single word of Cherokee. But because the core is classical and interpretable, the genome is
              legible and every bridge is logged, making the system a partner to play and argue with rather than an oracle
              to be trusted, and a way to ask, of any data stream, what we have chosen to hear.
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
