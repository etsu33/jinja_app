// QA 用の合成 fixture（本番ユーザーデータは含まない）
function rec(i, o = {}) {
  const names = ["QA第一神社", "QA第二神社", "QA第三神社", "QA第四神社"];
  const name = names[i - 1];
  return {
    id: 9000 + i, shrine_id: 9000 + i, recommendation_instance_id: `rid-qa-${i}`,
    name, display_name: name,
    address: `東京都千代田区テスト町${i}-${i}-${i} QAビルディング長い住所表記の折り返し確認用`,
    lat: 35.68 + i * 0.01, lng: 139.76 + i * 0.01, distance_m: 850 * i, duration_min: 12 * i,
    deities: ["天照大御神", "須佐之男命", "大国主命"].slice(0, 4 - i > 0 ? 4 - i : 1),
    tags: ["仕事運", "転機", "厄除け"],
    reason: `${name}は、転機を迎えた仕事の流れを整える場として選びました。`,
    reason_source: "reason:qa",
    history_theme: i === 1 ? "再出発" : null,
    trust_metadata: i === 1 ? { rank_class: "由緒あり", cultural_status: ["重要文化財", "都指定有形文化財"], lineage: "式内社", origin_summary: "古くから地域の信仰を集めてきたとされる神社です（QA用の合成文）。" } : null,
    explanation: { version: 1, summary: "仕事の転機という相談内容と、ご利益の一致を重視しました。", reasons: [{ code: "need_match", label: "悩みとの一致", text: "仕事運・転機のご利益が相談と一致しています。", strength: "high" }] },
    recommendation_reason_v4_detail: {
      version: "v4",
      reason_text: `${name}は仕事運と転機に関わる神社です。`,
      fact: { label: name, name, history_theme: "再出発", goriyaku: "仕事運", deity: "天照大御神", evidence: ["history_theme:再出発", "goriyaku:仕事運"] },
      interpretation: { theme: "再出発", text: "相談内容から、今扱いたいテーマを「区切りと再出発」と読み取っています。" },
      action: { text: "参拝前に、次の仕事で大切にしたい問いを一つに絞っておきます。" },
    },
    action_suggestion_v4_preview: {
      primary_action: { label: "まず詳細を見て、行く理由を確認する", description: "候補神社の詳細を見て判断材料を増やします。", action_type: "detail_open", confidence: 0.82 },
      secondary_action: { label: "候補として保存して、あとで見返す", description: "後から相談内容と一緒に見返せます。", action_type: "save", confidence: 0.74 },
      reflection_prompt: { question: "この神社に行くとしたら、何を整理する時間にしたいですか？", prompt_type: "before_visit", source_seed: "fallback" },
      action_source: { source: "fallback", reason: "QA" }, preview: true, version: "v4", source_keys: ["meaning_translation"],
    },
    direction_reference: i <= 2 ? { visit_date: "2026-11-03", actual_direction: "北東", reference_directions: ["北東", "南"], matched: i === 1, calculation_method: "annual_monthly_kyusei_v1", note: "QA用の参考方位です。" } : null,
    ...o,
  };
}
export const recs = [rec(1), rec(2), rec(3), rec(4)];
export const detail = {
  id: 500, title: "QA用テスト相談", last_message: "QA", last_message_at: "2026-10-22T00:00:00Z", message_count: 2,
  messages: [
    { id: 1, role: "user", content: "QA用テスト相談：転職を考えていて、仕事の流れを整えたいです。", created_at: "2026-10-22T00:00:00Z" },
    { id: 2, role: "assistant", content: "QA用の応答です。", created_at: "2026-10-22T00:00:01Z" },
  ],
  recommendations: recs, recommendations_v2: recs,
};
