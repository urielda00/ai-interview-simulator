export function getScoreMeaning(score, language = "en") {
  const numeric = Number(score || 0);

  if (language === "he") {
    if (numeric >= 9) {
      return {
        label: "מצוין",
        readiness: "מוכנות גבוהה מאוד לראיונות",
        tone: "excellent",
        explanation:
          "התשובות שלך כבר נראות ברמה טובה לראיונות אמיתיים. כדאי להמשיך ללטש עקביות, עומק ודיוק בתרחישים מורכבים.",
        strengths: ["תקשורת ברורה", "מבנה טכני טוב", "אינדיקציה חזקה למוכנות לראיונות"],
        improvements: ["להעמיק ב-edge cases", "לתרגל tradeoffs מערכתיים", "לחדד תשובות קצרות ומדויקות יותר"],
      };
    }

    if (numeric >= 7.5) {
      return {
        label: "חזק",
        readiness: "מוכנות טובה לראיונות",
        tone: "strong",
        explanation:
          "אתה בכיוון טוב. בהרבה ראיונות זה כבר יכול לעבור טוב, אבל יותר עומק, חידוד ודיוק ישפרו משמעותית את הסיכוי.",
        strengths: ["בסיס טוב", "תשובות יחסית ברורות", "סיגנל חיובי כללי"],
        improvements: ["לבנות תשובות במבנה ברור יותר", "להוסיף tradeoffs אמיתיים", "להעמיק תחת שאלות המשך"],
      };
    }

    if (numeric >= 6) {
      return {
        label: "בפיתוח",
        readiness: "מוכנות חלקית לראיונות",
        tone: "developing",
        explanation:
          "יש בסיס, אבל בראיונות אמיתיים זה עדיין עלול להרגיש לא יציב. כנראה צריך לשפר בהירות, ביטחון ועומק טכני.",
        strengths: ["יש הבנה התחלתית", "אפשר לראות פוטנציאל"],
        improvements: ["לתרגל תשובות מלאות ומסודרות", "להפחית ניסוחים עמומים", "לחזק יסודות טכניים"],
      };
    }

    return {
      label: "דורש חיזוק",
      readiness: "עדיין לא מוכן מספיק לראיונות",
      tone: "needs-work",
      explanation:
        "ברמה הזו ראיונות אמיתיים כנראה יחשפו פערים די מהר. כדאי לחזור ליסודות, למבנה תשובה ולתרגול עקבי לפני ראיונות חשובים.",
      strengths: ["אתה מזהה מוקדם איפה יש חולשות"],
      improvements: ["לחזק מושגי בסיס", "לתרגל דיבור ברור תחת לחץ", "לבסס יסודות לפני נושאים מתקדמים"],
    };
  }

  if (numeric >= 9) {
    return {
      label: "Excellent",
      readiness: "Very strong interview readiness",
      tone: "excellent",
      explanation:
        "Your answers look strong enough for real interview settings. Keep sharpening consistency and advanced tradeoff depth.",
      strengths: ["Clear communication", "Good technical structure", "Strong readiness signal for interviews"],
      improvements: ["Push deeper into edge cases", "Practice system-level tradeoffs", "Refine concise senior-style answers"],
    };
  }

  if (numeric >= 7.5) {
    return {
      label: "Strong",
      readiness: "Good interview readiness",
      tone: "strong",
      explanation:
        "You are on a solid path. In many interview situations this can already come across well, but stronger depth and sharper framing would improve outcomes.",
      strengths: ["Good baseline understanding", "Reasonably clear answers", "Positive overall signal"],
      improvements: ["Answer with clearer structure", "Add real-world tradeoffs", "Improve depth under follow-up questions"],
    };
  }

  if (numeric >= 6) {
    return {
      label: "Developing",
      readiness: "Partial interview readiness",
      tone: "developing",
      explanation:
        "There is a foundation, but in real interviews this level can still feel inconsistent. You likely need stronger clarity, confidence, and technical depth.",
      strengths: ["Some core understanding exists", "Potential is visible"],
      improvements: ["Practice complete structured answers", "Reduce vague explanations", "Study fundamentals more deeply"],
    };
  }

  return {
    label: "Needs work",
    readiness: "Not interview-ready yet",
    tone: "needs-work",
    explanation:
      "At this level, real interviews may expose gaps quickly. Focus on fundamentals, structure, and repeated practice before high-stakes interviews.",
    strengths: ["You are identifying weak areas early"],
    improvements: ["Rebuild core concepts", "Practice speaking clearly under pressure", "Review fundamentals before advanced topics"],
  };
}

export function getCategoryLabel(category, language = "en") {
  if (language === "he") {
    const mapping = {
      clarity: "בהירות",
      technical_accuracy: "דיוק טכני",
      depth: "עומק",
      tradeoff_reasoning: "חשיבת tradeoffs",
      correctness: "נכונות",
      complexity_analysis: "ניתוח סיבוכיות",
      data_structures: "מבני נתונים",
      communication: "תקשורת",
      architecture_reasoning: "חשיבה ארכיטקטונית",
      maintainability: "תחזוקתיות",
    };

    return mapping[category] || category;
  }

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

export function formatDuration(seconds, language = "en") {
  const total = Math.max(0, Math.round(Number(seconds || 0)));
  const minutes = Math.floor(total / 60);
  const remainingSeconds = total % 60;

  if (language === "he") {
    if (minutes === 0) return `${remainingSeconds} שנ'`;
    return `${minutes} דק' ${remainingSeconds} שנ'`;
  }

  if (minutes === 0) return `${remainingSeconds}s`;
  return `${minutes}m ${remainingSeconds}s`;
}

export function getTopCategories(breakdown = [], language = "en", limit = 2) {
  return [...breakdown]
    .filter((item) => typeof item?.score === "number")
    .sort((a, b) => b.score - a.score)
    .slice(0, limit)
    .map((item) => getCategoryLabel(item.category, language));
}

export function getBottomCategories(breakdown = [], language = "en", limit = 2) {
  return [...breakdown]
    .filter((item) => typeof item?.score === "number")
    .sort((a, b) => a.score - b.score)
    .slice(0, limit)
    .map((item) => getCategoryLabel(item.category, language));
}

export function getTrendLabel(current, previous, language = "en") {
  const curr = Number(current);
  const prev = Number(previous);

  if (!Number.isFinite(curr) || !Number.isFinite(prev)) {
    return language === "he" ? "אין מספיק נתונים" : "Not enough data";
  }

  const diff = curr - prev;

  if (diff >= 0.4) {
    return language === "he" ? "במגמת שיפור" : "Improving";
  }

  if (diff <= -0.4) {
    return language === "he" ? "יש ירידה לאחרונה" : "Recent drop";
  }

  return language === "he" ? "יציב יחסית" : "Relatively stable";
}

export function getDominantMode(history = [], language = "en") {
  const counts = history.reduce((acc, item) => {
    const mode = item?.mode || "standard";
    acc[mode] = (acc[mode] || 0) + 1;
    return acc;
  }, {});

  const top = Object.entries(counts).sort((a, b) => b[1] - a[1])[0];
  if (!top) return language === "he" ? "אין מספיק נתונים" : "Not enough data";

  return top[0];
}