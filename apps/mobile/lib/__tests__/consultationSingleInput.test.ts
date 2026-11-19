// docs/design/ios-ui-spec-v2.md 08節「1画面1テーマ」の契約。
//
// 相談の条件入力は相談画面(app/consultation/index.tsx)だけが持つ。
// 旧実装は Concierge にも ConditionFieldsCard を丸ごと置いており、
// 同じ入力が2箇所にあった。その形に戻らないことを検査する。
//
// 他の契約テストと同じく、画面のソースをテキストとして読む。
import { globSync, readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const mobileRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../..");

function read(relativePath: string) {
  return readFileSync(resolve(mobileRoot, relativePath), "utf8");
}

/** コメントを除いたコード本体。旧実装の名前は説明として残すため、検査からは外す。 */
function withoutComments(source: string): string {
  return source.replace(/\/\*[\s\S]*?\*\//g, "").replace(/\/\/.*$/gm, "");
}

const concierge = withoutComments(read("app/(tabs)/concierge/index.tsx"));
const consultation = withoutComments(read("app/consultation/index.tsx"));

// 相談画面から Concierge へ渡すクエリのキー。payload の契約そのものなので増減させない。
const CONDITION_KEYS = ["birthdate", "plannedVisitDate", "visitStyle", "goriyaku", "support"];

describe("条件入力の置き場所(08節)", () => {
  it("ConditionFieldsCard を使う画面は相談画面だけ", () => {
    const users = globSync(["app/**/*.tsx", "components/**/*.tsx"], { cwd: mobileRoot }).filter(
      (file) =>
        /<ConditionFieldsCard/.test(withoutComments(read(file))) &&
        file !== "components/ConditionFieldsCard.tsx",
    );

    expect(users).toEqual(["app/consultation/index.tsx"]);
  });

  it("Concierge は条件入力を持たず、相談画面へ送り返す", () => {
    expect(concierge).not.toContain("ConditionFieldsCard");
    expect(concierge).not.toContain("この条件で再提案する");
    expect(concierge).toContain("/consultation");
  });

  it("Concierge の「条件を変える」が相談画面を開く", () => {
    expect(concierge).toMatch(/openConsultation[\s\S]{0,600}?router\.push\(/);
    expect(concierge).toMatch(/onPress=\{openConsultation\}/);
  });
});

describe("条件の往復", () => {
  it("相談画面は Concierge から戻された条件をすべて受け取る", () => {
    const paramsBlock = consultation.match(/useLocalSearchParams<\{[\s\S]*?\}>\(\)/)?.[0] ?? "";
    expect(paramsBlock).not.toBe("");

    for (const key of [...CONDITION_KEYS, "q", "theme"]) {
      expect(paramsBlock).toContain(`${key}?: string`);
    }
  });

  it("相談画面は受け取った条件を初期値に入れる", () => {
    expect(consultation).toContain("params.birthdate ?? \"\"");
    expect(consultation).toContain("params.plannedVisitDate ?? \"\"");
    expect(consultation).toContain("params.support ?? \"\"");
    expect(consultation).toContain("params.visitStyle || undefined");
    expect(consultation).toContain("params.goriyaku || undefined");
    expect(consultation).toContain("params.theme || null");
    // 出発地点はクエリに載せずセッションで持つ(従来どおり)。復元元はそちら。
    expect(consultation).toContain("getOriginSession()");
  });

  it("Concierge は条件だけが変わった場合も再送信する", () => {
    // 相談画面は replace で戻るため、タブの画面インスタンスは生き残る。
    // 自動送信の判定キーが相談文だけだと、条件の変更が結果に反映されない。
    const key = concierge.match(/const paramsKey = \[[\s\S]*?\]/)?.[0] ?? "";
    expect(key).not.toBe("");

    for (const name of CONDITION_KEYS) {
      expect(key).toContain(`params.${name}`);
    }
  });

  it("Concierge は受け取った条件をそのまま送信に使う", () => {
    // state の更新はこのレンダーでは見えないので、params から作った値を直接渡す。
    expect(concierge).toMatch(/void submit\(initialQuery, incoming\)/);
    expect(concierge).toContain("goriyakuTagIds = await resolveGoriyakuTagIds(applied.goriyaku)");
    expect(concierge).toContain("visitStyleLabel: applied.visitStyle");
    expect(concierge).toContain("location: toOriginPayload(applied.origin)");
  });
});
