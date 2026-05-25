import { BriefView } from "./_brief/BriefView";
import { BRIEFS } from "./_brief/data";

export default function DailyBriefPage() {
  return <BriefView briefs={BRIEFS} />;
}
