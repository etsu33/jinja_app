// QA スクリプト共通の実行環境解決（環境依存の絶対パスを持たない）。
//
// - Playwright: apps/web の devDependency（@playwright/test）を、このファイルからの相対位置で解決する。
//   新しい依存は追加しない。先に `pnpm install` が必要。
// - Chromium: 既定は Playwright 管理のブラウザ（`pnpm --filter ./apps/web exec playwright install chromium`）。
//   バージョンの合わないブラウザしか無い環境では PLAYWRIGHT_CHROMIUM_EXECUTABLE で実行ファイルを指定する。
// - 対象サーバ: QA_BASE_URL（既定 http://localhost:3000。apps/web/playwright.config.ts の既定と同じ）。
import { createRequire } from "node:module";

const requireFromWeb = createRequire(new URL("../../../../apps/web/package.json", import.meta.url));

export const { chromium } = requireFromWeb("@playwright/test");

export const BASE_URL = (process.env.QA_BASE_URL || "http://localhost:3000").replace(/\/$/, "");

export function launchChromium() {
  const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || undefined;
  return chromium.launch(executablePath ? { executablePath } : {});
}
