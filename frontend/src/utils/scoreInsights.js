export function getScoreMeaning(score) {
  const numeric = Number(score || 0);

  if (numeric >= 9) {
    return {
      label: "Excellent",
      readiness: "Very strong interview readiness",
      tone: "excellent",
      explanation:
        "Your answers look strong enough for real interview settings. Keep sharpening consistency and advanced tradeoff depth.",
      strengths: [
        "Clear communication",
        "Good technical structure",
        "Strong readiness signal for interviews",
      ],
      improvements: [
        "Push deeper into edge cases",
        "Practice system-level tradeoffs",
        "Refine concise senior-style answers",
      ],
    };
  }

  if (numeric >= 7.5) {
    return {
      label: "Strong",
      readiness: "Good interview readiness",
      tone: "strong",
      explanation:
        "You are on a solid path. In many interview situations this can already come across well, but stronger depth and sharper framing would improve outcomes.",
      strengths: [
        "Good baseline understanding",
        "Reasonably clear answers",
        "Positive overall signal",
      ],
      improvements: [
        "Answer with clearer structure",
        "Add real-world tradeoffs",
        "Improve depth under follow-up questions",
      ],
    };
  }

  if (numeric >= 6) {
    return {
      label: "Developing",
      readiness: "Partial interview readiness",
      tone: "developing",
      explanation:
        "There is a foundation, but in real interviews this level can still feel inconsistent. You likely need stronger clarity, confidence, and technical depth.",
      strengths: [
        "Some core understanding exists",
        "Potential is visible",
      ],
      improvements: [
        "Practice complete structured answers",
        "Reduce vague explanations",
        "Study fundamentals more deeply",
      ],
    };
  }

  return {
    label: "Needs work",
    readiness: "Not interview-ready yet",
    tone: "needs-work",
    explanation:
      "At this level, real interviews may expose gaps quickly. Focus on fundamentals, structure, and repeated practice before high-stakes interviews.",
    strengths: [
      "You are identifying weak areas early",
    ],
    improvements: [
      "Rebuild core concepts",
      "Practice speaking clearly under pressure",
      "Review fundamentals before advanced topics",
    ],
  };
}

export function getCategoryLabel(category) {
  const mapping = {
    clarity: "Clarity",
    technical_accuracy: "Technical accuracy",
    depth: "Depth",
    tradeoff_reasoning: "Tradeoff reasoning",
    correctness: "Correctness",
    complexity_analysis: "Complexity analysis",
    data_structures: "Data structures",
    communication: "Communication",
    architecture_reasoning: "Architecture reasoning",
    maintainability: "Maintainability",
  };

  return mapping[category] || category;
}

export function formatDuration(seconds) {
  const total = Math.max(0, Math.round(Number(seconds || 0)));

  const minutes = Math.floor(total / 60);
  const remainingSeconds = total % 60;

  if (minutes === 0) return `${remainingSeconds}s`;
  return `${minutes}m ${remainingSeconds}s`;
}