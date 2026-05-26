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
  { id: "operator",   name: "Operator",   color: "var(--lens-operator)",   ink: "var(--lens-operator-ink)" },
];

export type Claim = { n: number; text: string; src: string };

export type Brief = {
  id: string;
  lens: LensId;
  lenses?: LensId[];
  title: string;
  lead: string;
  why: string;
  source_count: number;
  read_min: number;
  sources: string[];
  claims: Claim[];
};
