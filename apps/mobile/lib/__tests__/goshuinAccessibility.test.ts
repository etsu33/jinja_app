import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

const upload = readFileSync(new URL("../../app/goshuin/upload.tsx", import.meta.url), "utf8");
const list = readFileSync(new URL("../../app/goshuin/index.tsx", import.meta.url), "utf8");

describe("御朱印のアクセシビリティと保存時の通知", () => {
  it.each([
    ["takePhoto", "カメラで御朱印を撮影する"],
    ["pickFromLibrary", "アルバムから御朱印画像を選択する"],
  ])("%s を名前付きボタンとして公開する", (handler, label) => {
    const button = upload.match(/<Pressable\b[\s\S]*?<\/Pressable>/g)
      ?.find((block) => block.includes(`onPress={${handler}}`));
    expect(button).toContain('accessibilityRole="button"');
    expect(button).toContain(`accessibilityLabel="${label}"`);
  });

  it("プレビューと保存済み画像を名前付き画像として公開する", () => {
    const preview = upload.match(/<Image\b[^>]*\/>/)?.[0];
    expect(preview).toMatch(/style=\{styles\.previewImage\}\s+accessible\s/);
    expect(preview).toContain('accessibilityRole="image"');
    expect(preview).toContain('accessibilityLabel="選択した御朱印画像"');

    const savedImage = list.match(/stamps\.map\(\(s, index\) => \(\s*(<Image\b[^>]*\/>)/)?.[1];
    expect(savedImage).toMatch(/\saccessible\s/);
    expect(savedImage).toContain('accessibilityRole="image"');
    expect(savedImage).toContain('accessibilityLabel={`御朱印の記録 ${index + 1}件目`}');
  });

  it("保存の成功時に通知して戻り、結果なしと例外では失敗を通知する", () => {
    const save = upload.match(/const save = async \(\) => \{[\s\S]*?\n  \};/)?.[0];
    expect(save).toMatch(/const savedItem = await pushStamp\(uri\);\s*if \(!savedItem\) \{\s*showSaveFailure\(\);\s*return;\s*\}/);
    expect(save).toMatch(/Alert\.alert\("保存しました"\);\s*goBack\(\);/);
    expect(save).toMatch(/catch \(error\) \{[\s\S]*?\n\s*\}\s*showSaveFailure\(\);\s*\} finally/);
    expect(upload).toMatch(/function showSaveFailure\(\) \{\s*Alert\.alert\("保存できませんでした", "時間をおいて、もう一度お試しください。"\);\s*\}/);
  });

  it("画面マウント時の権限リクエストを維持する", () => {
    expect(upload).toMatch(/const ask = React\.useCallback\(async \(\) => \{\s*await ImagePicker\.requestCameraPermissionsAsync\(\);\s*await ImagePicker\.requestMediaLibraryPermissionsAsync\(\);\s*\}, \[\]\);/);
    expect(upload).toMatch(/React\.useEffect\(\(\) => \{\s*ask\(\);\s*\}, \[ask\]\);/);
  });

  it("既存の撮影・画像選択オプションとキャンセル時の処理を維持する", () => {
    expect(upload).toMatch(/const pickFromLibrary = async \(\) => \{\s*const res = await ImagePicker\.launchImageLibraryAsync\(\{\s*mediaTypes: ImagePicker\.MediaTypeOptions\.Images,\s*quality: 0\.9,\s*\}\);\s*if \(!res\.canceled\) setUri\(res\.assets\[0\]\.uri\);\s*\};/);
    expect(upload).toMatch(/const takePhoto = async \(\) => \{\s*const res = await ImagePicker\.launchCameraAsync\(\{ quality: 0\.9 \}\);\s*if \(!res\.canceled\) setUri\(res\.assets\[0\]\.uri\);\s*\};/);
  });
});
