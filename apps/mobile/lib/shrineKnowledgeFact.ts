// apps/mobile/lib/shrineKnowledgeFact.ts
//
// Backend Shrine Detail API（backend/temples/api/serializers/shrine.py）が返す
// Knowledge Fact（deities/histories）を、Mobile Shrine Detail画面向けの
// ViewModelへ変換する。
//
// Evidence判定（usable/full/disputed/hiddenの決定）はここでは一切行わない。
// Backendはhidden相当のFactを既にレスポンスから除外しており、ここへ届くのは
// full相当（source_confirmed/reviewed + ready Source）またはdisputed相当
// （disputed + ready Source）のFactのみという前提に立つ（PR-M1）。
//
// apps/web/src/lib/api/types.ts / apps/web/src/lib/shrine/buildShrineFactSection.ts
// と概念を揃える（full/disputedの2状態、verification_status→表示状態の変換を
// 1箇所へ集約するという方針）。コード自体は共有しない（Web=DOM/Tailwind、
// Mobile=React Native View/StyleSheetでレンダリング層が異なるため）。

// --- API Types（backend/temples/api/serializers/shrine.py に一致する） ---

export type ShrineKnowledgeSource = {
  id: number;
  source_type: string;
  title: string;
  publisher: string;
  url: string;
  verification_status: string;
  confidence: string;
};

export type ShrineDeity = {
  id: number;
  display_name: string;
  canonical_name: string;
  role: string;
  sort_order: number;
  verification_status: string;
  confidence: string;
  sources: ShrineKnowledgeSource[];
};

export type ShrineHistory = {
  id: number;
  history_type: string;
  title: string;
  content: string;
  period_text: string;
  event_date: string | null;
  sort_order: number;
  verification_status: string;
  confidence: string;
  sources: ShrineKnowledgeSource[];
};

// --- ViewModel ---

// hiddenはBackendで除外済みのため、Mobile ViewModelへは持ち込まない。
export type FactDisplayState = "full" | "disputed";

export type FactDeityViewModel = {
  displayName: string;
  sortOrder: number;
  confidence: string;
  sources: ShrineKnowledgeSource[];
  displayState: FactDisplayState;
};

export type FactHistoryViewModel = {
  historyType: string;
  title: string;
  content: string;
  periodText: string;
  sortOrder: number;
  confidence: string;
  sources: ShrineKnowledgeSource[];
  displayState: FactDisplayState;
};

export type ShrineFactViewModel = {
  deities: FactDeityViewModel[];
  histories: FactHistoryViewModel[];
};

// Backend verification_status → Mobile ViewModel専用のFactDisplayStateへ変換する
// 唯一の地点。将来のUI実装(PR-M2)はこの変換結果だけを見て、Backendの
// verification_status文字列を各所で直接判定しない。想定外の値が来た場合は
// disputedへ昇格させずfullとして扱う（fail-safe。Webのresolve関数と同じ方針）。
// confidence/history_typeはこの判定に使わない。
export function resolveFactDisplayState(verificationStatus: string): FactDisplayState {
  return verificationStatus === "disputed" ? "disputed" : "full";
}

function bySortOrder<T extends { sort_order: number }>(items: T[]): T[] {
  return [...items].sort((a, b) => a.sort_order - b.sort_order);
}

// deities/historiesを、Mobile Shrine Detail向けのViewModelへ変換する。
// Fact本文（display_name/title/content/period_text等）・confidence・sourcesは
// 加工せずそのまま保持する。sourcesはSource UI未実装のため今回は表示に使わないが、
// 将来のSource UI実装に備え内部型としては保持する。複数のFactは常に別要素の
// ままとし、自動統合・自動要約・自動グルーピングは行わない。
export function buildShrineFactViewModel(shrine: {
  deities?: ShrineDeity[];
  histories?: ShrineHistory[];
}): ShrineFactViewModel {
  const deities = Array.isArray(shrine.deities) ? shrine.deities : [];
  const histories = Array.isArray(shrine.histories) ? shrine.histories : [];

  return {
    deities: bySortOrder(deities).map((deity) => ({
      displayName: deity.display_name,
      sortOrder: deity.sort_order,
      confidence: deity.confidence,
      sources: deity.sources,
      displayState: resolveFactDisplayState(deity.verification_status),
    })),
    histories: bySortOrder(histories).map((history) => ({
      historyType: history.history_type,
      title: history.title,
      content: history.content,
      periodText: history.period_text,
      sortOrder: history.sort_order,
      confidence: history.confidence,
      sources: history.sources,
      displayState: resolveFactDisplayState(history.verification_status),
    })),
  };
}

// UI（PR-M2）向けの表示条件判定。UI側でverification_status/displayStateの
// 比較をJSX内へ散らさないための唯一の判定地点とする。
export function isDisputedDisplayState(displayState: FactDisplayState): boolean {
  return displayState === "disputed";
}

// Knowledge Fact Section自体を表示するかどうかの判定。deities/historiesが
// 両方空の場合はfalseを返し、UI側はセクション全体を非表示にする
// （Legacy「神社について」は本判定と無関係に従来通り表示され続ける）。
export function hasVisibleKnowledgeFact(viewModel: ShrineFactViewModel): boolean {
  return viewModel.deities.length > 0 || viewModel.histories.length > 0;
}
