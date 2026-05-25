export type LensId = "founder" | "engineer" | "researcher" | "operator" | "investor";

export type Lens = {
  id: LensId;
  name: string;
  color: string;
  ink: string;
};

export const LENSES: Lens[] = [
  { id: "founder",    name: "Founder",    color: "var(--lens-founder)",    ink: "var(--lens-founder-ink)" },
  { id: "engineer",   name: "Engineer",   color: "var(--lens-engineer)",   ink: "var(--lens-engineer-ink)" },
  { id: "researcher", name: "Researcher", color: "var(--lens-researcher)", ink: "var(--lens-researcher-ink)" },
];

export type Claim = { n: number; text: string; src: string };

export type Brief = {
  id: string;
  lens: LensId;
  title: string;
  lead: string;
  why: string;
  source_count: number;
  read_min: number;
  sources: string[];
  claims: Claim[];
};

export const BRIEFS: Brief[] = [
  {
    id: "b1",
    lens: "founder",
    title: "Anthropic raised $13B at $183B post — three signals for B2B fintech",
    lead: "The deck's go-to-market section mentions India explicitly. Enterprise revenue mix is shifting toward $1M+ contracts. The round closed in nine days.",
    why: "Your thesis is on agentic workflows for SMB payroll. The pricing data point sets a ceiling on what your customers will tolerate from upstream LLM costs — and the GTM hint suggests Anthropic will compete for your distribution.",
    source_count: 12,
    read_min: 4,
    sources: ["information.com", "anthropic.com/news", "theinformation.com", "pitchbook.com"],
    claims: [
      { n: 1, text: "Round closed in <em>nine days</em>, oversubscribed at $183B post-money.", src: "theinformation.com · funding desk · ¶3" },
      { n: 2, text: "Enterprise revenue mix shifted toward $1M+ contracts (now ~40% of ARR).", src: "anthropic.com · investor letter · ¶7" },
      { n: 3, text: "India go-to-market named in the deck — first time on record.", src: "theinformation.com · slide 14" },
    ],
  },
  {
    id: "b2",
    lens: "engineer",
    title: "Speculative decoding gets a 200-line reference implementation",
    lead: "It's small enough to read in a sitting. The trick is the rejection-sampling math, not the throughput numbers — those depend entirely on draft-model quality.",
    why: "You're going deep on agentic systems where latency dominates UX. This is the cleanest writeup of the technique to date, and worth understanding before you decide whether to bake it in.",
    source_count: 8,
    read_min: 6,
    sources: ["github.com/karpathy", "news.ycombinator.com", "arxiv.org/abs/2503"],
    claims: [
      { n: 1, text: "200-line PyTorch reference — runs on a single 3090.", src: "github.com/karpathy · README" },
      { n: 2, text: "Throughput gain caps at ~2.4× and falls off sharply with poor draft models.", src: "arxiv.org/abs/2503 · table 4" },
      { n: 3, text: "Open question: <em>does the gain hold under structured outputs?</em>", src: "r/MachineLearning · top comment" },
    ],
  },
  {
    id: "b3",
    lens: "researcher",
    title: "CHI papers converge on interaction-first accessibility",
    lead: "Three papers this week land on the same insight: traditional WCAG is necessary but not sufficient. The new question is interaction grammar, not contrast ratio.",
    why: "You're exploring assistive HCI. The convergence between teams that don't cite each other yet is signal — there's a synthesis paper waiting to be written.",
    source_count: 4,
    read_min: 8,
    sources: ["arxiv.org", "dl.acm.org/chi", "a11ymatters.org"],
    claims: [
      { n: 1, text: "CMU and UW independently propose \"interaction-first\" accessibility frameworks.", src: "arxiv.org/abs/2502.10934" },
      { n: 2, text: "Both treat screen-reader users as the primary persona, not an accommodation.", src: "dl.acm.org/chi/2026/14" },
      { n: 3, text: "Neither paper cites the other (yet). <em>Probably will by ASSETS.</em>", src: "analysis" },
    ],
  },
  {
    id: "b4",
    lens: "founder",
    title: "Razorpay and PhonePe both shipped agent SDKs this week",
    lead: "Two of India's three largest payments players now publish agent-callable APIs. The third has the docs in draft.",
    why: "Your moat assumption was that integration friction protected you. That moat just got narrower — and the smart move is to be on top of these SDKs before your customers ask.",
    source_count: 6,
    read_min: 3,
    sources: ["razorpay.com/blog", "phonepe.com/dev", "inc42.com"],
    claims: [],
  },
  {
    id: "b5",
    lens: "engineer",
    title: "PyTorch 2.6 lands — torch.compile cache survives across processes",
    lead: "The headline number is a 3× cold-start improvement in their benchmark. The real story is that the cache is now portable between machines.",
    why: "If you're building an inference service with autoscaling, this changes your warm-up math. Worth a half-day spike to measure on your model.",
    source_count: 5,
    read_min: 2,
    sources: ["pytorch.org/blog", "github.com/pytorch"],
    claims: [],
  },
];
