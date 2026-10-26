#!/usr/bin/env node
// apps/web/scripts/audit/bff-backend-call-graph.mjs
//
// WS-04 BFF Backend call-graph audit（read-only static analysis）.
//
// apps/web/src 以下の全 .ts / .tsx を TypeScript Compiler API で解析し、静的に辿れる HTTP request site を列挙する。
// 各 site について「Backend へ届くか」「WS-04 HMAC client identity（clientIdentityHeaders）が付く可能性があるか」を分類する。
//
// - fetch / globalThis.fetch / window.fetch / 別名・bind・再 export は checker の symbol 解決で辿る。
// - URL が引数に依存する関数は wrapper として扱い、その呼び出し元を request site として再評価する（推移的）。
// - 署名 helper の存在は「条件付き署名（conditionally signed）」であり、実際に署名された証明ではない。
// - 解決できない呼び出しは安全と見なさず unresolved に入れる。
// - 出力には env の「名前」だけを含める。値・secret・IP・token・署名は読まない / 出さない。
//
// 使い方:
//   node scripts/audit/bff-backend-call-graph.mjs                 # summary を stdout へ
//   node scripts/audit/bff-backend-call-graph.mjs --json out.json --md out.md
//   node scripts/audit/bff-backend-call-graph.mjs --check out.json # 生成結果と既存 JSON の差分検査

import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";
import ts from "typescript";

export const BACKEND_ENV_NAMES = Object.freeze([
  "DJANGO_ORIGIN",
  "BACKEND_ORIGIN",
  "DJANGO_API_BASE_URL",
  "BACKEND_BASE_URL",
  "BACKEND_URL",
]);
export const APP_ENV_NAMES = Object.freeze([
  "WEB_BASE_URL",
  "PLAYWRIGHT_BASE_URL",
  "VERCEL_URL",
  "VERCEL_PROJECT_PRODUCTION_URL",
  "NEXT_PUBLIC_APP_URL",
  "NEXT_PUBLIC_BASE_URL",
]);
// どちらを指すかが deployment の設定次第で、名前からは決められないもの。
export const AMBIGUOUS_ENV_NAMES = Object.freeze(["NEXT_PUBLIC_API_BASE_URL", "NEXT_PUBLIC_API_BASE"]);

const SIGNING_HELPER = "clientIdentityHeaders";
const KNOWN_WRAPPERS = Object.freeze(["djFetch", "bffFetchWithAuthFromReq", "bffPostJsonWithAuthFromReq"]);
const ROUTE_METHODS = new Set(["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]);
const AXIOS_REQUEST_METHODS = new Set([
  "request",
  "get",
  "delete",
  "head",
  "options",
  "post",
  "put",
  "patch",
  "postForm",
  "putForm",
  "patchForm",
]);
const AUTH_HEADER_NAMES = new Set(["authorization", "cookie", "x-csrftoken", "x-csrf-token"]);
const MAX_DEPTH = 10;

const ROUTE_RE = /^app\/(.+\/)?route\.(ts|tsx)$/;
const SSR_ENTRY_RE =
  /^app\/(.+\/)?(page|layout|template|default|loading|error|global-error|not-found|opengraph-image|twitter-image|icon|apple-icon|sitemap|robots|manifest)\.(ts|tsx)$/;
const TEST_RE = /(^|\/)(__tests__|tests|__mocks__)\/|\.(test|spec)\.(ts|tsx)$|^mocks\//;
const STORY_RE = /\.stories\.(ts|tsx)$/;

// ---------------------------------------------------------------------------
// Program construction
// ---------------------------------------------------------------------------

function walkSourceFiles(dir) {
  const out = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) out.push(...walkSourceFiles(full));
    else if (/\.(ts|tsx)$/.test(entry.name) && !entry.name.endsWith(".d.ts")) out.push(full);
  }
  return out;
}

/** apps/web の tsconfig を使い、src 以下の全 .ts / .tsx（tsconfig の exclude を含む）を root にする。 */
export function createProgramFromDisk(webRoot) {
  const configPath = path.join(webRoot, "tsconfig.json");
  const config = ts.readConfigFile(configPath, ts.sys.readFile);
  if (config.error) throw new Error(ts.flattenDiagnosticMessageText(config.error.messageText, "\n"));
  const parsed = ts.parseJsonConfigFileContent(config.config, ts.sys, webRoot);
  const srcDir = path.join(webRoot, "src");
  const rootNames = walkSourceFiles(srcDir).sort();
  const options = { ...parsed.options, noEmit: true, incremental: false, plugins: undefined };
  delete options.tsBuildInfoFile;
  const program = ts.createProgram({ rootNames, options });
  return { program, srcDir, rootNames };
}

/** test 用: メモリ上の file map（root からの相対 path → source）から program を作る。 */
export function createProgramFromFiles(files, { rootDir = "/virtual" } = {}) {
  const abs = new Map(Object.entries(files).map(([k, v]) => [path.posix.join(rootDir, k), v]));
  const dirs = new Set();
  for (const f of abs.keys()) {
    let d = path.posix.dirname(f);
    while (d !== "/" && !dirs.has(d)) {
      dirs.add(d);
      d = path.posix.dirname(d);
    }
  }
  const options = {
    target: ts.ScriptTarget.ES2022,
    module: ts.ModuleKind.ESNext,
    moduleResolution: ts.ModuleResolutionKind.Bundler,
    strict: true,
    noEmit: true,
    skipLibCheck: true,
    lib: ["lib.es2022.d.ts", "lib.dom.d.ts"],
    types: [],
    baseUrl: rootDir,
    paths: { "@/*": ["./src/*"] },
  };
  const host = ts.createCompilerHost(options, true);
  const original = host.getSourceFile.bind(host);
  host.getSourceFile = (fileName, languageVersion, onError, shouldCreate) =>
    abs.has(fileName)
      ? ts.createSourceFile(fileName, abs.get(fileName), languageVersion, true)
      : original(fileName, languageVersion, onError, shouldCreate);
  host.fileExists = (f) => abs.has(f) || (!f.startsWith(`${rootDir}/`) && ts.sys.fileExists(f));
  host.readFile = (f) => (abs.has(f) ? abs.get(f) : ts.sys.readFile(f));
  host.directoryExists = (d) =>
    dirs.has(d) || (!d.startsWith(`${rootDir}/`) && d !== rootDir && ts.sys.directoryExists(d));
  host.getDirectories = (d) => (dirs.has(d) ? [] : ts.sys.getDirectories(d));
  const rootNames = [...abs.keys()].filter((f) => f.startsWith(`${rootDir}/src/`) && /\.(ts|tsx)$/.test(f)).sort();
  const program = ts.createProgram({ rootNames, options, host });
  return { program, srcDir: path.posix.join(rootDir, "src"), rootNames };
}

// ---------------------------------------------------------------------------
// Analysis
// ---------------------------------------------------------------------------

function isInside(file, dir) {
  const rel = path.relative(dir, file);
  return rel !== "" && !rel.startsWith("..") && !path.isAbsolute(rel);
}

function unwrap(e) {
  while (
    e &&
    (ts.isParenthesizedExpression(e) ||
      ts.isAsExpression(e) ||
      ts.isNonNullExpression(e) ||
      ts.isTypeAssertionExpression(e) ||
      ts.isSatisfiesExpression(e))
  ) {
    e = e.expression;
  }
  return e;
}

function isFunctionLike(n) {
  return (
    !!n &&
    (ts.isFunctionDeclaration(n) ||
      ts.isFunctionExpression(n) ||
      ts.isArrowFunction(n) ||
      ts.isMethodDeclaration(n) ||
      ts.isGetAccessorDeclaration(n) ||
      ts.isConstructorDeclaration(n))
  );
}

function enclosingFunctions(node) {
  const out = [];
  for (let p = node.parent; p; p = p.parent) if (isFunctionLike(p)) out.push(p);
  return out;
}

function shortText(node, max = 140) {
  const t = node.getText().replace(/\s+/g, " ").trim();
  return t.length > max ? `${t.slice(0, max - 1)}…` : t;
}

function isStringLike(type) {
  return (type.flags & ts.TypeFlags.StringLike) !== 0;
}

function isNullish(node) {
  const e = unwrap(node);
  return (
    !e ||
    e.kind === ts.SyntaxKind.NullKeyword ||
    (ts.isIdentifier(e) && e.text === "undefined") ||
    ts.isVoidExpression(e)
  );
}

function isProcessEnv(e) {
  e = unwrap(e);
  return (
    ts.isPropertyAccessExpression(e) &&
    e.name.text === "env" &&
    ts.isIdentifier(unwrap(e.expression)) &&
    unwrap(e.expression).text === "process"
  );
}

function setUnion(...sets) {
  const out = new Set();
  for (const s of sets) for (const v of s) out.add(v);
  return out;
}

function sorted(set) {
  return [...set].sort();
}

export function analyzeProgram(program, { srcDir }) {
  const checker = program.getTypeChecker();
  const sourceFiles = program
    .getSourceFiles()
    .filter((sf) => !sf.isDeclarationFile && isInside(sf.fileName, srcDir))
    .sort((a, b) => (a.fileName < b.fileName ? -1 : 1));
  const projectFileSet = new Set(sourceFiles);
  const rel = (sf) => path.relative(srcDir, sf.fileName).split(path.sep).join("/");
  const scopeOf = (sf) => (TEST_RE.test(rel(sf)) ? "test" : STORY_RE.test(rel(sf)) ? "storybook" : "production");
  const isProjectNode = (n) => projectFileSet.has(n.getSourceFile());
  const loc = (node) => {
    const sf = node.getSourceFile();
    const { line, character } = sf.getLineAndCharacterOfPosition(node.getStart(sf));
    return { file: `src/${rel(sf)}`, line: line + 1, column: character + 1 };
  };

  // ---- module facts -------------------------------------------------------
  const moduleInfo = new Map();
  for (const sf of sourceFiles) {
    const directives = new Set();
    for (const st of sf.statements) {
      if (ts.isExpressionStatement(st) && ts.isStringLiteral(st.expression)) directives.add(st.expression.text);
      else break;
    }
    let serverOnly = false;
    for (const st of sf.statements) {
      if (
        ts.isImportDeclaration(st) &&
        ts.isStringLiteral(st.moduleSpecifier) &&
        st.moduleSpecifier.text === "server-only"
      ) {
        serverOnly = true;
      }
    }
    const r = rel(sf);
    moduleInfo.set(sf, {
      rel: r,
      scope: scopeOf(sf),
      useClient: directives.has("use client"),
      useServer: directives.has("use server"),
      serverOnly,
      isRoute: ROUTE_RE.test(r),
      isSsrEntry: SSR_ENTRY_RE.test(r),
      imports: new Set(),
      labels: new Set(),
    });
  }

  function moduleOfSpecifier(spec) {
    const s = checker.getSymbolAtLocation(spec);
    const d = s?.valueDeclaration ?? s?.declarations?.[0];
    return d && ts.isSourceFile(d) && projectFileSet.has(d) ? d : null;
  }

  for (const sf of sourceFiles) {
    const info = moduleInfo.get(sf);
    const add = (spec) => {
      const target = spec && ts.isStringLiteralLike(spec) ? moduleOfSpecifier(spec) : null;
      if (target) info.imports.add(target);
    };
    for (const st of sf.statements) {
      if (ts.isImportDeclaration(st) && !st.importClause?.isTypeOnly) add(st.moduleSpecifier);
      if (ts.isExportDeclaration(st) && st.moduleSpecifier && !st.isTypeOnly) add(st.moduleSpecifier);
    }
    const visitDyn = (n) => {
      if (ts.isCallExpression(n) && n.expression.kind === ts.SyntaxKind.ImportKeyword) add(n.arguments[0]);
      ts.forEachChild(n, visitDyn);
    };
    visitDyn(sf);
  }

  // Next.js entrypoint から import を辿って実行 context を付ける。
  {
    const queue = [];
    for (const [sf, info] of moduleInfo) {
      if (info.scope !== "production") continue;
      if (info.isRoute) queue.push([sf, "route-handler"]);
      if (info.isSsrEntry) queue.push([sf, info.useClient ? "client" : "ssr"]);
    }
    while (queue.length) {
      const [sf, label] = queue.shift();
      const info = moduleInfo.get(sf);
      if (info.labels.has(label)) continue;
      info.labels.add(label);
      for (const target of info.imports) {
        const ti = moduleInfo.get(target);
        const next = ti.useClient ? "client" : ti.useServer ? "server-action" : label;
        if (!ti.labels.has(next)) queue.push([target, next]);
      }
    }
  }

  // ---- reference index（関数単位の到達性と context） ---------------------
  const refIndex = new Map();
  for (const sf of sourceFiles) {
    if (moduleInfo.get(sf).scope !== "production") continue;
    const visit = (n) => {
      if (ts.isIdentifier(n)) {
        const p = n.parent;
        const isDeclName =
          (ts.isFunctionDeclaration(p) ||
            ts.isVariableDeclaration(p) ||
            ts.isMethodDeclaration(p) ||
            ts.isParameter(p)) &&
          p.name === n;
        const isSpecifier = ts.isImportSpecifier(p) || ts.isExportSpecifier(p) || ts.isImportClause(p);
        if (!isDeclName && !isSpecifier) {
          let sym = checker.getSymbolAtLocation(n);
          if (sym && sym.flags & ts.SymbolFlags.Alias) {
            try {
              sym = checker.getAliasedSymbol(sym);
            } catch {
              sym = undefined;
            }
          }
          if (sym) {
            if (!refIndex.has(sym)) refIndex.set(sym, []);
            refIndex.get(sym).push(n);
          }
        }
      }
      ts.forEachChild(n, visit);
    };
    visit(sf);
  }

  function symbolOfFunction(fn) {
    const nameNode = fn.name ?? (fn.parent && ts.isVariableDeclaration(fn.parent) ? fn.parent.name : null);
    return nameNode && ts.isIdentifier(nameNode) ? checker.getSymbolAtLocation(nameNode) : undefined;
  }

  function isEntryExport(fn) {
    const info = moduleInfo.get(fn.getSourceFile());
    const name = functionName(fn);
    if (info.isRoute && ROUTE_METHODS.has(name)) return true;
    if (info.isSsrEntry) {
      const isDefault =
        ts.getCombinedModifierFlags(fn.parent && ts.isVariableDeclaration(fn.parent) ? fn.parent : fn) &
        ts.ModifierFlags.Default;
      if (
        isDefault ||
        ts.isExportAssignment(fn.parent) ||
        ["generateMetadata", "generateStaticParams", "generateViewport"].includes(name)
      )
        return true;
      // export default Foo; の形
      const sym = symbolOfFunction(fn);
      if (
        sym &&
        fn
          .getSourceFile()
          .statements.some(
            (st) =>
              ts.isExportAssignment(st) &&
              ts.isIdentifier(st.expression) &&
              checker.getSymbolAtLocation(st.expression) === sym,
          )
      )
        return true;
    }
    return false;
  }

  /** site を囲む最上位関数の参照元 module から context を決める（module 単位より細かい近似）。 */
  function siteContext(node) {
    const sf = node.getSourceFile();
    const moduleCtx = contextOf(sf);
    const chain = enclosingFunctions(node);
    const top = chain[chain.length - 1];
    if (!top || moduleInfo.get(sf).scope !== "production") return { ...moduleCtx, functionReferenced: null };
    // "use client" module の関数はブラウザで動く（server page から JSX で参照されていても）。
    const pinned = moduleInfo.get(sf).useClient || moduleInfo.get(sf).useServer || moduleInfo.get(sf).isRoute;
    if (isEntryExport(top)) return { ...moduleCtx, functionReferenced: true };
    const sym = symbolOfFunction(top);
    if (!sym) return { ...moduleCtx, functionReferenced: null };
    const refs = refIndex.get(sym) ?? [];
    if (!refs.length) return { labels: moduleCtx.labels, reachable: false, functionReferenced: false };
    if (pinned) return { ...moduleCtx, functionReferenced: true };
    const labels = new Set();
    for (const ref of refs) {
      const rsf = ref.getSourceFile();
      if (rsf === sf) for (const l of moduleCtx.labels) labels.add(l);
      else for (const l of contextOf(rsf).labels) labels.add(l);
    }
    const reachable = refs.some((ref) => contextOf(ref.getSourceFile()).reachable);
    return { labels: sorted(labels), reachable, functionReferenced: true };
  }

  function contextOf(sf) {
    const info = moduleInfo.get(sf);
    if (info.labels.size) return { labels: sorted(info.labels), reachable: true };
    const fallback = info.isRoute
      ? "route-handler"
      : info.useServer
        ? "server-action"
        : info.useClient
          ? "client"
          : info.serverOnly
            ? "server"
            : "unknown";
    return { labels: [fallback], reachable: false };
  }

  // ---- symbol / callee resolution ---------------------------------------
  function symbolAt(e) {
    e = unwrap(e);
    if (!e) return undefined;
    const target = ts.isPropertyAccessExpression(e) ? e.name : e;
    // `{ refresh }` の name は property symbol ではなく値の symbol を見る。
    let s =
      e.parent && ts.isShorthandPropertyAssignment(e.parent) && e.parent.name === e
        ? checker.getShorthandAssignmentValueSymbol(e.parent)
        : checker.getSymbolAtLocation(target);
    if (!s && ts.isElementAccessExpression(e) && ts.isStringLiteralLike(e.argumentExpression)) {
      s = checker.getTypeAtLocation(e.expression).getProperty(e.argumentExpression.text);
    }
    if (s && s.flags & ts.SymbolFlags.Alias) {
      try {
        s = checker.getAliasedSymbol(s);
      } catch {
        /* unresolved alias */
      }
    }
    return s;
  }

  function isGlobalFetchSymbol(s) {
    return (
      !!s &&
      s.name === "fetch" &&
      !!s.declarations?.length &&
      s.declarations.every((d) => d.getSourceFile().isDeclarationFile) &&
      s.declarations.some(
        (d) =>
          ts.isFunctionDeclaration(d) ||
          ts.isVariableDeclaration(d) ||
          ts.isMethodSignature(d) ||
          ts.isPropertySignature(d),
      )
    );
  }

  function isAxiosType(type) {
    const candidates = [
      type.aliasSymbol,
      type.getSymbol(),
      ...(type.isIntersection() ? type.types.map((t) => t.getSymbol()) : []),
    ];
    return candidates.some((s) => {
      const d = s?.declarations?.[0];
      return (
        !!d &&
        /[\\/]node_modules[\\/]axios[\\/]/.test(d.getSourceFile().fileName) &&
        /^(Axios|AxiosInstance|AxiosStatic)$/.test(s.name)
      );
    });
  }

  function isNextHeadersFn(s, names) {
    const d = s?.declarations?.[0];
    return !!d && names.includes(s.name) && /[\\/]next[\\/]/.test(d.getSourceFile().fileName);
  }

  const calleeCache = new Map();
  function resolveCallee(calleeExpr, depth = 0) {
    if (depth === 0 && calleeCache.has(calleeExpr)) return calleeCache.get(calleeExpr);
    const r = resolveCalleeUncached(calleeExpr, depth);
    if (depth === 0) calleeCache.set(calleeExpr, r);
    return r;
  }

  function resolveCalleeUncached(calleeExpr, depth) {
    const e = unwrap(calleeExpr);
    if (depth > 6) return { kind: "dynamic", reason: "alias chain too deep" };
    if (ts.isPropertyAccessExpression(e) && (e.name.text === "call" || e.name.text === "apply")) {
      const inner = resolveCallee(e.expression, depth + 1);
      if (inner.kind === "global-fetch" || inner.kind === "project-fn") {
        return { ...inner, argShift: e.name.text === "call" ? 1 : null, viaCallApply: e.name.text };
      }
    }
    if (
      ts.isPropertyAccessExpression(e) &&
      AXIOS_REQUEST_METHODS.has(e.name.text) &&
      isAxiosType(checker.getTypeAtLocation(e.expression))
    ) {
      return { kind: "axios", method: e.name.text, receiver: e.expression };
    }
    if (!ts.isPropertyAccessExpression(e) && isAxiosType(checker.getTypeAtLocation(e))) {
      return { kind: "axios", method: "request", receiver: e };
    }
    if ((ts.isArrowFunction(e) || ts.isFunctionExpression(e)) && isProjectNode(e))
      return { kind: "project-fn", fn: e, name: "<iife>" };
    if (ts.isCallExpression(e))
      return { kind: "dynamic", reason: `callee is the return value of ${shortText(e.expression, 40)}(...)` };
    const s = symbolAt(e);
    if (!s) return { kind: "dynamic", reason: "callee symbol not resolvable" };
    if (isGlobalFetchSymbol(s)) return { kind: "global-fetch" };
    const decl = s.valueDeclaration ?? s.declarations?.[0];
    if (!decl) return { kind: "dynamic", reason: "callee has no declaration" };
    if (isFunctionLike(decl) && isProjectNode(decl)) return { kind: "project-fn", fn: decl, name: s.name };
    if (ts.isVariableDeclaration(decl) && isProjectNode(decl)) {
      if (!decl.initializer) return { kind: "dynamic", reason: `variable '${s.name}' has no initializer` };
      const init = unwrap(decl.initializer);
      if (ts.isArrowFunction(init) || ts.isFunctionExpression(init))
        return { kind: "project-fn", fn: init, name: s.name };
      let target = init;
      if (
        ts.isCallExpression(target) &&
        ts.isPropertyAccessExpression(target.expression) &&
        target.expression.name.text === "bind"
      ) {
        target = target.expression.expression;
      }
      // React.useCallback(fn, deps) は fn そのものを返す。
      if (
        ts.isCallExpression(target) &&
        /(^|\.)useCallback$/.test(target.expression.getText()) &&
        target.arguments[0]
      ) {
        const cb = unwrap(target.arguments[0]);
        if (ts.isArrowFunction(cb) || ts.isFunctionExpression(cb)) return { kind: "project-fn", fn: cb, name: s.name };
        target = cb;
      }
      const inner = resolveCallee(target, depth + 1);
      if (inner.kind === "other") return inner;
      const isConst = (decl.parent.flags & ts.NodeFlags.Const) !== 0;
      return { ...inner, alias: s.name, reassignable: !isConst };
    }
    if (
      isProjectNode(decl) &&
      (ts.isParameter(decl) ||
        ts.isBindingElement(decl) ||
        ts.isPropertySignature(decl) ||
        ts.isPropertyDeclaration(decl) ||
        ts.isPropertyAssignment(decl) ||
        ts.isShorthandPropertyAssignment(decl))
    ) {
      return { kind: "dynamic", reason: `callee '${s.name}' is a ${ts.SyntaxKind[decl.kind]}` };
    }
    return { kind: "other", name: s.name, symbol: s };
  }

  function functionName(fn) {
    if (ts.isConstructorDeclaration(fn)) return "constructor";
    if (fn.name && (ts.isIdentifier(fn.name) || ts.isStringLiteral(fn.name))) return fn.name.text;
    const p = fn.parent;
    if (p && ts.isVariableDeclaration(p) && ts.isIdentifier(p.name)) return p.name.text;
    if (p && (ts.isPropertyAssignment(p) || ts.isPropertyDeclaration(p)) && p.name) return p.name.getText();
    if (p && ts.isExportAssignment(p)) return "default export";
    if (p && ts.isCallExpression(p)) return `<callback:${shortText(p.expression, 40)}>`;
    return "<anonymous>";
  }

  function qualifiedName(node) {
    const chain = enclosingFunctions(node).reverse();
    return chain.length ? chain.map(functionName).join(" > ") : "(module scope)";
  }

  function isRouteHandlerExport(fn) {
    const sf = fn.getSourceFile();
    if (!moduleInfo.get(sf)?.isRoute) return false;
    return ROUTE_METHODS.has(functionName(fn)) && enclosingFunctions(fn).length === 0;
  }

  function returnExpressions(fn) {
    if (!fn.body) return [];
    if (!ts.isBlock(fn.body)) return [fn.body];
    const out = [];
    const visit = (n) => {
      if (isFunctionLike(n)) return;
      if (ts.isReturnStatement(n) && n.expression) out.push(n.expression);
      ts.forEachChild(n, visit);
    };
    ts.forEachChild(fn.body, visit);
    return out;
  }

  const assignmentCache = new Map();
  function assignmentsOf(symbol, decl) {
    if (assignmentCache.has(symbol)) return assignmentCache.get(symbol);
    let scope = decl;
    while (scope && !isFunctionLike(scope) && !ts.isSourceFile(scope)) scope = scope.parent;
    const out = [];
    const visit = (n) => {
      if (
        ts.isBinaryExpression(n) &&
        n.operatorToken.kind === ts.SyntaxKind.EqualsToken &&
        ts.isIdentifier(n.left) &&
        symbolAt(n.left) === symbol
      ) {
        out.push(n.right);
      }
      ts.forEachChild(n, visit);
    };
    if (scope) visit(scope);
    assignmentCache.set(symbol, out);
    return out;
  }

  // ---- value facts --------------------------------------------------------
  function newFacts() {
    return {
      env: new Set(),
      literals: [],
      params: [],
      optionProps: [],
      calls: new Set(),
      signingCalls: [],
      hostHeader: false,
      nextHeaders: false,
      objectKeys: new Set(),
      truncated: false,
    };
  }

  function mergeFacts(into, from, { withParams = true } = {}) {
    for (const v of from.env) into.env.add(v);
    into.literals.push(...from.literals);
    if (withParams) into.params.push(...from.params);
    into.optionProps.push(...from.optionProps);
    for (const v of from.calls) into.calls.add(v);
    into.signingCalls.push(...from.signingCalls);
    for (const v of from.objectKeys) into.objectKeys.add(v);
    into.hostHeader ||= from.hostHeader;
    into.nextHeaders ||= from.nextHeaders;
    into.truncated ||= from.truncated;
  }

  const ROOT_CTX = { subst: new Map(), id: 0 };
  let ctxCounter = 0;

  function collectFacts(expr, ctx = ROOT_CTX, startDepth = 0) {
    const facts = newFacts();
    const seen = new Set();
    const visit = (node, c, depth) => {
      if (!node) return;
      if (depth > MAX_DEPTH) {
        facts.truncated = true;
        return;
      }
      const key = `${node.getSourceFile().fileName}:${node.pos}:${node.end}:${c.id}`;
      if (seen.has(key)) return;
      seen.add(key);

      if (ts.isStringLiteralLike(node)) {
        facts.literals.push(node.text);
        if (node.text === "host" || node.text === "x-forwarded-host") facts.hostHeader = true;
        return;
      }
      if (ts.isTemplateExpression(node)) {
        facts.literals.push(node.head.text);
        for (const span of node.templateSpans) {
          visit(span.expression, c, depth + 1);
          facts.literals.push(span.literal.text);
        }
        return;
      }
      if (isFunctionLike(node)) return;
      if (ts.isPropertyAccessExpression(node)) {
        if (isProcessEnv(node.expression)) {
          facts.env.add(node.name.text);
          return;
        }
        visit(node.expression, c, depth + 1);
        return;
      }
      if (ts.isElementAccessExpression(node)) {
        if (isProcessEnv(node.expression) && ts.isStringLiteralLike(node.argumentExpression)) {
          facts.env.add(node.argumentExpression.text);
          return;
        }
        visit(node.expression, c, depth + 1);
        visit(node.argumentExpression, c, depth + 1);
        return;
      }
      if (ts.isIdentifier(node)) {
        visitIdentifier(node, c, depth);
        return;
      }
      if (ts.isShorthandPropertyAssignment(node)) {
        facts.objectKeys.add(node.name.text.toLowerCase());
        visitIdentifier(node.name, c, depth);
        return;
      }
      if (ts.isCallExpression(node)) {
        const r = resolveCallee(node.expression);
        if (r.kind === "project-fn" && r.name === SIGNING_HELPER) {
          facts.signingCalls.push({ call: node, ctx: c });
          return;
        }
        if (r.kind === "project-fn") {
          facts.calls.add(r.name);
          const subst = new Map(c.subst);
          subst.set(r.fn, { args: node.arguments, callerCtx: c });
          const inner = { subst, id: ++ctxCounter };
          for (const ret of returnExpressions(r.fn)) visit(ret, inner, depth + 1);
          return;
        }
        if (r.kind === "other" && isNextHeadersFn(r.symbol, ["headers"])) {
          facts.nextHeaders = true;
          return;
        }
        if (r.kind === "other" && isNextHeadersFn(r.symbol, ["cookies"])) {
          facts.calls.add("cookies");
          return;
        }
        if (ts.isPropertyAccessExpression(node.expression)) {
          const lit = node.arguments[0];
          if (node.expression.name.text === "get" && lit && ts.isStringLiteralLike(lit)) {
            if (lit.text === "host" || lit.text === "x-forwarded-host") facts.hostHeader = true;
          }
          visit(node.expression.expression, c, depth + 1);
        }
        for (const a of node.arguments) visit(a, c, depth + 1);
        return;
      }
      if (ts.isConditionalExpression(node)) {
        visit(node.whenTrue, c, depth + 1);
        visit(node.whenFalse, c, depth + 1);
        return;
      }
      if (ts.isObjectLiteralExpression(node)) {
        for (const p of node.properties) {
          if (ts.isPropertyAssignment(p)) {
            const k = p.name
              .getText()
              .replace(/^["']|["']$/g, "")
              .toLowerCase();
            facts.objectKeys.add(k);
            visit(p.initializer, c, depth + 1);
          } else if (ts.isShorthandPropertyAssignment(p)) {
            visit(p, c, depth + 1);
          } else if (ts.isSpreadAssignment(p)) {
            visit(p.expression, c, depth + 1);
          }
        }
        return;
      }
      ts.forEachChild(node, (child) => visit(child, c, depth + 1));
    };

    const visitIdentifier = (id, c, depth) => {
      if (id.text === "undefined") return;
      const s = symbolAt(id);
      const decl = s?.valueDeclaration ?? s?.declarations?.[0];
      if (!decl) return;
      if (ts.isParameter(decl) && isFunctionLike(decl.parent)) {
        const fn = decl.parent;
        const index = fn.parameters.indexOf(decl);
        const sub = c.subst.get(fn);
        if (sub) {
          if (sub.args[index]) visit(sub.args[index], sub.callerCtx, depth + 1);
          if (decl.initializer) visit(decl.initializer, c, depth + 1);
          return;
        }
        facts.params.push({
          fn,
          index,
          name: decl.name.getText(),
          optional: !!decl.questionToken || !!decl.initializer,
        });
        if (decl.initializer) visit(decl.initializer, c, depth + 1);
        return;
      }
      if (ts.isBindingElement(decl)) {
        const prop = (decl.propertyName ?? decl.name).getText();
        let container = decl.parent.parent;
        while (container && ts.isBindingElement(container)) container = container.parent.parent;
        // 分割代入の元を別 facts に集め、引数 param は option property として記録する。
        const sub = collectFactsFrom(container, c, depth);
        for (const p of sub.params) facts.optionProps.push({ fn: p.fn, index: p.index, prop, name: p.name });
        mergeFacts(facts, sub, { withParams: false });
        if (decl.initializer) visit(decl.initializer, c, depth + 1);
        return;
      }
      if (ts.isVariableDeclaration(decl)) {
        if (!isProjectNode(decl)) return;
        if (decl.initializer) visit(decl.initializer, c, depth + 1);
        if ((decl.parent.flags & ts.NodeFlags.Const) === 0) {
          for (const rhs of assignmentsOf(s, decl)) visit(rhs, c, depth + 1);
        }
        return;
      }
      if (
        (ts.isPropertyAssignment(decl) || ts.isPropertyDeclaration(decl)) &&
        isProjectNode(decl) &&
        decl.initializer
      ) {
        visit(decl.initializer, c, depth + 1);
      }
    };

    const collectFactsFrom = (container, c, depth) => {
      const out = newFacts();
      if (!container) return out;
      if (ts.isVariableDeclaration(container) && container.initializer) {
        mergeFacts(out, collectFactsInner(container.initializer, c, depth + 1));
      } else if (ts.isParameter(container) && isFunctionLike(container.parent)) {
        const fn = container.parent;
        const index = fn.parameters.indexOf(container);
        const sub = c.subst.get(fn);
        if (sub && sub.args[index]) mergeFacts(out, collectFactsInner(sub.args[index], sub.callerCtx, depth + 1));
        else out.params.push({ fn, index, name: container.name.getText(), optional: !!container.questionToken });
      }
      return out;
    };

    const collectFactsInner = (node, c, depth) => collectFacts(node, c, depth);

    visit(expr, ctx, startDepth);
    return facts;
  }

  // ---- URL decomposition -------------------------------------------------
  function urlElements(expr, depth = 0) {
    const e = unwrap(expr);
    if (!e) return [];
    if (depth > 8) return [{ type: "expr", node: e }];
    if (ts.isStringLiteralLike(e)) return [{ type: "lit", text: e.text }];
    if (ts.isTemplateExpression(e)) {
      const out = [];
      if (e.head.text) out.push({ type: "lit", text: e.head.text });
      for (const span of e.templateSpans) {
        out.push(...urlElements(span.expression, depth + 1));
        if (span.literal.text) out.push({ type: "lit", text: span.literal.text });
      }
      return out;
    }
    if (ts.isBinaryExpression(e) && e.operatorToken.kind === ts.SyntaxKind.PlusToken) {
      return [...urlElements(e.left, depth + 1), ...urlElements(e.right, depth + 1)];
    }
    if (ts.isNewExpression(e) && ts.isIdentifier(e.expression) && e.expression.text === "URL" && e.arguments?.length) {
      const [p, b] = e.arguments;
      return b ? [...urlElements(b, depth + 1), ...urlElements(p, depth + 1)] : urlElements(p, depth + 1);
    }
    if (
      ts.isCallExpression(e) &&
      ts.isPropertyAccessExpression(e.expression) &&
      e.expression.name.text === "toString" &&
      e.arguments.length === 0
    ) {
      return urlElements(e.expression.expression, depth + 1);
    }
    if (ts.isPropertyAccessExpression(e) && e.name.text === "href") return urlElements(e.expression, depth + 1);
    if (
      ts.isCallExpression(e) &&
      ts.isIdentifier(e.expression) &&
      e.expression.text === "String" &&
      e.arguments.length === 1
    ) {
      return urlElements(e.arguments[0], depth + 1);
    }
    if (ts.isIdentifier(e)) {
      const s = symbolAt(e);
      const d = s?.valueDeclaration;
      if (
        d &&
        ts.isVariableDeclaration(d) &&
        isProjectNode(d) &&
        d.initializer &&
        d.parent.flags & ts.NodeFlags.Const
      ) {
        return urlElements(d.initializer, depth + 1);
      }
    }
    return [{ type: "expr", node: e }];
  }

  const isPathLiteral = (t) => t.startsWith("/") || t.startsWith("?");
  const BACKEND_LITERAL_RE = /^https?:\/\/(127\.0\.0\.1|localhost):8000|^https?:\/\/[a-z0-9-]+\.onrender\.com/i;

  /**
   * URL を base（origin を決める部分）と path に分け、base の分類と path の静的形を返す。
   * owners: 引数依存を判定する対象の関数（site を囲む関数）。
   */
  function analyzeUrl(urlExpr, owners, { baseOverride = null } = {}) {
    const els = urlExpr ? urlElements(urlExpr) : [];
    const base = [];
    const pathEls = [];
    let started = false;
    for (let i = 0; i < els.length; i++) {
      const el = els[i];
      if (started) {
        pathEls.push(el);
        continue;
      }
      if (el.type === "lit") {
        const abs = /^(https?:\/\/[^/?#]*)(.*)$/i.exec(el.text);
        if (abs) {
          base.push({ type: "lit", text: abs[1] });
          if (abs[2]) {
            started = true;
            pathEls.push({ type: "lit", text: abs[2] });
          }
        } else if (isPathLiteral(el.text)) {
          started = true;
          pathEls.push(el);
        } else {
          base.push(el);
        }
        continue;
      }
      el.facts = collectFacts(el.node);
      const next = els[i + 1];
      const nextIsPath = !!next && next.type === "lit" && isPathLiteral(next.text);
      const baseLike =
        el.facts.env.size > 0 ||
        el.facts.hostHeader ||
        el.facts.literals.some((l) => /^https?:\/\//i.test(l) || l === "://") ||
        nextIsPath;
      const pathLike = !baseLike && el.facts.literals.some((l) => isPathLiteral(l));
      if (baseLike && !pathLike) base.push(el);
      else {
        started = true;
        pathEls.push(el);
      }
    }
    for (const el of pathEls) if (el.type === "expr" && !el.facts) el.facts = collectFacts(el.node);

    const ownerSet = new Set(owners);
    const paramsOf = (el) => (el.type === "expr" ? el.facts.params.filter((p) => ownerSet.has(p.fn)) : []);
    const firstPath = pathEls[0];
    const pathParamOwners = firstPath ? paramsOf(firstPath) : [];
    const baseParams = base.flatMap(paramsOf);

    const env = new Set();
    let host = false;
    let backendLiteral = false;
    let externalLiteral = null;
    let relativeDefault = false;
    for (const el of base) {
      if (el.type === "lit") {
        if (BACKEND_LITERAL_RE.test(el.text)) backendLiteral = true;
        else if (/^https?:\/\//i.test(el.text)) externalLiteral = el.text;
        continue;
      }
      for (const v of el.facts.env) env.add(v);
      host ||= el.facts.hostHeader;
      for (const l of el.facts.literals) {
        if (BACKEND_LITERAL_RE.test(l)) backendLiteral = true;
        if (l === "/api" || l === "/api/") relativeDefault = true;
      }
    }
    const backendEnv = [...env].filter((v) => BACKEND_ENV_NAMES.includes(v));
    const appEnv = [...env].filter((v) => APP_ENV_NAMES.includes(v));
    const ambiguousEnv = [...env].filter((v) => AMBIGUOUS_ENV_NAMES.includes(v));
    const backendSide = backendEnv.length > 0 || backendLiteral;
    const appSide = appEnv.length > 0 || host;

    let category;
    if (baseOverride) category = baseOverride;
    else if (!base.length) {
      if (firstPath?.type === "lit" && firstPath.text.startsWith("/")) category = "relative";
      else if (pathParamOwners.length) category = "parameter";
      else category = "unresolved";
    } else if (backendSide && (appSide || relativeDefault)) category = "backend-or-internal";
    else if (backendSide) category = "backend";
    else if (appSide) category = "internal-bff";
    else if (ambiguousEnv.length && relativeDefault) category = "relative-env-overridable";
    else if (ambiguousEnv.length) category = "ambiguous-env";
    else if (externalLiteral) category = "external";
    else if (baseParams.length) category = "parameter";
    else category = "unresolved";

    const staticPath = pathEls
      .map((el) => (el.type === "lit" ? el.text : "{*}"))
      .join("")
      .replace(/\{\*\}(\{\*\})+/g, "{*}");

    return {
      category,
      staticPath: staticPath || (pathEls.length ? "{*}" : ""),
      pathDynamic: !!firstPath && firstPath.type === "expr",
      pathParamOwners,
      baseParams,
      envNames: sorted(env),
      backendEnv,
      appEnv,
      ambiguousEnv,
      backendLiteral,
      hostHeader: host,
      externalLiteral,
      expression: urlExpr ? shortText(urlExpr) : "(none)",
    };
  }

  // ---- collect every call expression ------------------------------------
  const allCalls = [];
  const callsByFn = new Map();
  const escapedRefs = [];
  for (const sf of sourceFiles) {
    const visit = (n) => {
      if (ts.isCallExpression(n) && n.expression.kind !== ts.SyntaxKind.ImportKeyword) {
        const r = resolveCallee(n.expression);
        allCalls.push({ node: n, r, sf });
        if (r.kind === "project-fn") {
          if (!callsByFn.has(r.fn)) callsByFn.set(r.fn, []);
          callsByFn.get(r.fn).push(n);
        }
      }
      if (ts.isIdentifier(n) && n.text === "fetch") {
        const p = n.parent;
        const isCallee =
          (ts.isCallExpression(p) && p.expression === n) ||
          (ts.isPropertyAccessExpression(p) &&
            p.name === n &&
            ts.isCallExpression(p.parent) &&
            p.parent.expression === p) ||
          (ts.isPropertyAccessExpression(p) && p.expression === n && ["call", "apply", "bind"].includes(p.name.text));
        const isDeclOrType =
          ts.isTypeQueryNode(p) ||
          ts.isQualifiedName(p) ||
          (ts.isPropertyAccessExpression(p) &&
            p.expression === n &&
            !["call", "apply", "bind"].includes(p.name.text)) ||
          ((ts.isFunctionDeclaration(p) ||
            ts.isMethodDeclaration(p) ||
            ts.isPropertyAssignment(p) ||
            ts.isPropertySignature(p) ||
            ts.isMethodSignature(p) ||
            ts.isVariableDeclaration(p) ||
            ts.isParameter(p) ||
            ts.isBindingElement(p) ||
            ts.isShorthandPropertyAssignment(p)) &&
            p.name === n);
        const isAliasInit = ts.isVariableDeclaration(p) && p.initializer === n;
        if (!isCallee && !isDeclOrType && !isAliasInit && isGlobalFetchSymbol(symbolAt(n))) {
          escapedRefs.push({ node: n, sf });
        }
      }
      ts.forEachChild(n, visit);
    };
    visit(sf);
  }

  const productionCallers = (fn) =>
    (callsByFn.get(fn) ?? []).filter((c) => moduleInfo.get(c.getSourceFile()).scope === "production");

  // 関数が値として渡されている（呼び出し以外で参照されている）箇所
  function escapedFunctionRefs(fn) {
    const out = [];
    const nameNode = fn.name ?? (ts.isVariableDeclaration(fn.parent) ? fn.parent.name : null);
    if (!nameNode || !ts.isIdentifier(nameNode)) return out;
    const target = checker.getSymbolAtLocation(nameNode);
    if (!target) return out;
    for (const sf of sourceFiles) {
      const visit = (n) => {
        if (ts.isIdentifier(n) && n.text === nameNode.text && n !== nameNode) {
          const p = n.parent;
          const isCallee = ts.isCallExpression(p) && p.expression === n;
          const isImportExport = ts.isImportSpecifier(p) || ts.isExportSpecifier(p) || ts.isImportClause(p);
          if (!isCallee && !isImportExport && symbolAt(n) === target) out.push(n);
        }
        ts.forEachChild(n, visit);
      };
      visit(sf);
    }
    return out;
  }

  // ---- request items: sinks first, then wrappers to a fixed point --------
  const items = [];
  const itemByNode = new Map();
  const wrappers = new Map();

  function argsOf(call, r) {
    const args = [...call.arguments];
    if (r.argShift) args.shift();
    return args;
  }

  function urlAndInitOfSink(call, r) {
    const args = argsOf(call, r);
    if (r.kind === "global-fetch") return { urlExpr: args[0], initExpr: args[1] };
    // axios
    const m = r.method;
    if (m === "request") {
      const cfg = args[0] && resolveObjectLiteral(args[0]);
      const urlProp = cfg && findProp(cfg, "url");
      return {
        urlExpr: urlProp ?? (args[0] && !cfg ? args[0] : undefined),
        initExpr: args[1] ?? args[0],
        axiosBase: axiosBaseOf(r.receiver),
      };
    }
    const configIndex = ["post", "put", "patch", "postForm", "putForm", "patchForm"].includes(m) ? 2 : 1;
    return { urlExpr: args[0], initExpr: args[configIndex], axiosBase: axiosBaseOf(r.receiver) };
  }

  function resolveObjectLiteral(expr, depth = 0) {
    const e = unwrap(expr);
    if (!e || depth > 4) return null;
    if (ts.isObjectLiteralExpression(e)) return e;
    if (ts.isIdentifier(e)) {
      const s = symbolAt(e);
      const d = s?.valueDeclaration;
      if (
        d &&
        ts.isVariableDeclaration(d) &&
        d.initializer &&
        isProjectNode(d) &&
        d.parent.flags & ts.NodeFlags.Const
      ) {
        return resolveObjectLiteral(d.initializer, depth + 1);
      }
    }
    return null;
  }

  function findProp(obj, name) {
    for (const p of obj.properties) {
      if (ts.isPropertyAssignment(p) && p.name.getText().replace(/^["']|["']$/g, "") === name) return p.initializer;
      if (ts.isShorthandPropertyAssignment(p) && p.name.text === name) return p.name;
    }
    return undefined;
  }

  function hasSpread(obj) {
    return obj.properties.some((p) => ts.isSpreadAssignment(p));
  }

  function axiosBaseOf(receiver) {
    const s = symbolAt(receiver);
    const d = s?.valueDeclaration;
    if (d && ts.isVariableDeclaration(d) && d.initializer) {
      const init = unwrap(d.initializer);
      if (
        ts.isCallExpression(init) &&
        ts.isPropertyAccessExpression(init.expression) &&
        init.expression.name.text === "create"
      ) {
        const cfg = init.arguments[0] && resolveObjectLiteral(init.arguments[0]);
        return cfg ? (findProp(cfg, "baseURL") ?? null) : null;
      }
    }
    return null;
  }

  function methodOf(initExpr, r) {
    if (r.kind === "axios")
      return r.method === "request" ? "dynamic(config.method)" : r.method.replace(/Form$/, "").toUpperCase();
    if (!initExpr) return "GET";
    const ue = unwrap(initExpr);
    if (ts.isConditionalExpression(ue)) {
      const both = new Set([methodOf(ue.whenTrue, r), methodOf(ue.whenFalse, r)]);
      return both.size === 1 ? [...both][0] : `one of ${sorted(both).join(" / ")}`;
    }
    const obj = resolveObjectLiteral(initExpr);
    if (!obj) return `from ${shortText(initExpr, 40)}`;
    const m = findProp(obj, "method");
    if (m) {
      const u = unwrap(m);
      if (ts.isStringLiteralLike(u)) return u.text.toUpperCase();
      return `dynamic(${shortText(m, 50)})`;
    }
    return hasSpread(obj) ? "GET unless overridden by spread init" : "GET";
  }

  function signingCallsInBodies(call, upTo) {
    const out = [];
    for (const fn of enclosingFunctions(call)) {
      const visit = (n) => {
        if (ts.isCallExpression(n)) {
          const r = resolveCallee(n.expression);
          if (r.kind === "project-fn" && r.name === SIGNING_HELPER)
            out.push({ call: n, ctx: ROOT_CTX, where: "function-body" });
        }
        ts.forEachChild(n, visit);
      };
      if (fn.body) visit(fn.body);
      if (fn === upTo) break;
    }
    return out;
  }

  function topNamedFunction(node) {
    const chain = enclosingFunctions(node);
    return chain[chain.length - 1] ?? null;
  }

  function wrapperCandidateOwner(analysis) {
    const owners = analysis.pathParamOwners.length
      ? analysis.pathParamOwners
      : analysis.category === "parameter"
        ? analysis.baseParams
        : [];
    for (const p of owners) {
      const fn = p.fn;
      // Route Handler の export は Next.js が呼ぶ entrypoint であり wrapper ではない。
      if (isRouteHandlerExport(fn)) continue;
      if (productionCallers(fn).length > 0) {
        return { fn, indices: [...new Set(owners.filter((o) => o.fn === fn).map((o) => o.index))] };
      }
    }
    return null;
  }

  function registerWrapper(fn, urlIndices, innerItem) {
    let w = wrappers.get(fn);
    const fresh = !w;
    if (!w) {
      const sf = fn.getSourceFile();
      w = {
        fn,
        name: functionName(fn),
        file: loc(fn).file,
        line: loc(fn).line,
        urlParamIndices: new Set(),
        innerItems: [],
        model: null,
      };
      wrappers.set(fn, w);
      void sf;
    }
    for (const i of urlIndices) w.urlParamIndices.add(i);
    w.innerItems.push(innerItem);
    return fresh;
  }

  // phase A: discover
  const queue = [];
  for (const c of allCalls) {
    if (c.r.kind === "global-fetch" || c.r.kind === "axios") queue.push({ kind: "sink", node: c.node, r: c.r });
  }
  while (queue.length) {
    const item = queue.shift();
    if (itemByNode.has(item.node)) continue;
    itemByNode.set(item.node, item);
    items.push(item);
    const owners = enclosingFunctions(item.node);
    if (item.kind === "sink") {
      const { urlExpr, initExpr, axiosBase } = urlAndInitOfSink(item.node, item.r);
      item.urlExpr = urlExpr;
      item.initExpr = initExpr;
      item.url = axiosBase && urlExpr ? analyzeAxiosUrl(axiosBase, urlExpr, owners) : analyzeUrl(urlExpr, owners);
    } else {
      const w = wrappers.get(item.wrapperFn);
      const args = argsOf(item.node, item.r);
      item.urlArgIndex = pickUrlArg(args, w.urlParamIndices);
      item.urlExpr = args[item.urlArgIndex];
      item.url = analyzeUrl(item.urlExpr, owners);
    }
    const owner = wrapperCandidateOwner(item.url);
    if (owner) {
      item.internalTo = owner.fn;
      const fresh = registerWrapper(owner.fn, owner.indices, item);
      if (fresh) {
        for (const call of callsByFn.get(owner.fn) ?? []) {
          const r = resolveCallee(call.expression);
          queue.push({ kind: "wrapper-call", node: call, r, wrapperFn: owner.fn });
        }
      }
    }
  }

  function analyzeAxiosUrl(baseExpr, urlExpr, owners) {
    const u = unwrap(urlExpr);
    if (ts.isStringLiteralLike(u) && /^https?:\/\//i.test(u.text)) return analyzeUrl(urlExpr, owners);
    const baseA = analyzeUrl(baseExpr, owners);
    const pathA = analyzeUrl(urlExpr, owners);
    // axios は baseURL と相対 URL を "/" で連結する（"action-events/" → "<baseURL>/action-events/"）。
    if (ts.isStringLiteralLike(u) && !u.text.startsWith("/")) pathA.staticPath = `/${u.text}`;
    const basePath = baseA.staticPath || "";
    return {
      ...pathA,
      category: baseA.category === "relative" ? "relative" : baseA.category,
      staticPath: `${basePath}${pathA.staticPath}`.replace(/\/\//g, "/"),
      envNames: setUnion(baseA.envNames, pathA.envNames).size ? sorted(setUnion(baseA.envNames, pathA.envNames)) : [],
      ambiguousEnv: baseA.ambiguousEnv,
      expression: `${shortText(baseExpr, 60)} + ${shortText(urlExpr, 60)}`,
      axiosBaseCategory: baseA.category,
    };
  }

  function pickUrlArg(args, indices) {
    const list = sorted(indices)
      .map(Number)
      .sort((a, b) => a - b);
    for (const i of list) {
      if (args[i] && isStringLike(checker.getTypeAtLocation(args[i]))) return i;
    }
    return list[0] ?? 0;
  }

  // phase B: wrapper models（signing / auth / base）
  function identitySourcesFromSigningCalls(signingCalls, fn) {
    const sources = [];
    for (const sc of signingCalls) {
      const arg = sc.call.arguments[0];
      if (!arg || isNullish(arg)) continue;
      const f = collectFacts(arg, sc.ctx);
      for (const p of f.params) if (p.fn === fn) sources.push({ type: "param", index: p.index, name: p.name });
      for (const o of f.optionProps) if (o.fn === fn) sources.push({ type: "option", index: o.index, prop: o.prop });
      if (f.nextHeaders) sources.push({ type: "next-headers" });
    }
    return dedupeSources(sources);
  }

  function dedupeSources(sources) {
    const seen = new Set();
    return sources.filter((s) => {
      const k = JSON.stringify(s);
      if (seen.has(k)) return false;
      seen.add(k);
      return true;
    });
  }

  function authFeaturesOfFunction(fn) {
    const headerNames = new Set();
    const sourceParams = new Set();
    const gates = new Set();
    const visit = (n) => {
      if (ts.isCallExpression(n) && ts.isPropertyAccessExpression(n.expression)) {
        const name = n.expression.name.text;
        const lit = n.arguments[0];
        if (lit && ts.isStringLiteralLike(lit)) {
          const v = lit.text.toLowerCase();
          if (name === "set" && AUTH_HEADER_NAMES.has(v)) headerNames.add(v);
          const recv = unwrap(n.expression.expression);
          const isIncoming =
            ts.isPropertyAccessExpression(recv) && (recv.name.text === "headers" || recv.name.text === "cookies");
          if (
            name === "get" &&
            isIncoming &&
            (AUTH_HEADER_NAMES.has(v) || v === "access_token" || v === "refresh_token")
          ) {
            const f = collectFacts(recv.expression);
            for (const p of f.params) if (p.fn === fn) sourceParams.add(p.index);
          }
        }
      }
      if (ts.isPropertyAssignment(n) || ts.isShorthandPropertyAssignment(n)) {
        const k = n.name
          .getText()
          .replace(/^["']|["']$/g, "")
          .toLowerCase();
        if (AUTH_HEADER_NAMES.has(k)) headerNames.add(k);
      }
      if (ts.isBindingElement(n) || ts.isPropertyAccessExpression(n)) {
        const nm = ts.isBindingElement(n) ? (n.propertyName ?? n.name).getText() : n.name.text;
        if (/^forward.*auth/i.test(nm)) gates.add(nm);
      }
      ts.forEachChild(n, visit);
    };
    if (fn.body) visit(fn.body);
    return { headerNames, sourceParams, gates };
  }

  const modelInProgress = new Set();
  function modelOf(w) {
    if (w.model) return w.model;
    if (modelInProgress.has(w.fn))
      return {
        base: "unresolved",
        prefix: "",
        sources: [],
        helper: false,
        auth: { headerNames: new Set(), sourceParams: new Set(), gates: new Set() },
        cyclic: true,
      };
    modelInProgress.add(w.fn);
    const bases = new Set();
    let sources = [];
    let helper = false;
    const evidence = [];
    const auth = { headerNames: new Set(), sourceParams: new Set(), gates: new Set() };
    const finalSinks = [];
    const prefixes = new Set();
    const own = authFeaturesOfFunction(w.fn);
    for (const v of own.headerNames) auth.headerNames.add(v);
    for (const v of own.sourceParams) auth.sourceParams.add(v);
    for (const v of own.gates) auth.gates.add(v);
    for (const inner of w.innerItems) {
      if (inner.kind === "sink") {
        bases.add(inner.url.category);
        const initFacts = inner.initExpr ? collectFacts(inner.initExpr) : newFacts();
        for (const k of initFacts.objectKeys) if (AUTH_HEADER_NAMES.has(k)) auth.headerNames.add(k);
        const signing = [
          ...initFacts.signingCalls.map((s) => ({ ...s, where: "init" })),
          ...signingCallsInBodies(inner.node, w.fn),
        ];
        if (signing.length) helper = true;
        for (const s of signing)
          evidence.push(
            `${SIGNING_HELPER}(${shortText(s.call.arguments[0] ?? s.call, 40)}) at ${loc(s.call).file}:${loc(s.call).line} [${s.where}]`,
          );
        sources.push(...identitySourcesFromSigningCalls(signing, w.fn));
        finalSinks.push(`${loc(inner.node).file}:${loc(inner.node).line}`);
        prefixes.add(inner.url.staticPath.split("{*}")[0]);
      } else {
        const innerW = wrappers.get(inner.wrapperFn);
        const m = modelOf(innerW);
        bases.add(m.base === "parameter" ? inner.url.category : m.base);
        if (m.helper) helper = true;
        evidence.push(`delegates to ${innerW.name} at ${loc(inner.node).file}:${loc(inner.node).line}`);
        finalSinks.push(...m.finalSinks);
        prefixes.add(`${m.prefix}${inner.url.staticPath.split("{*}")[0]}`);
        const args = argsOf(inner.node, inner.r);
        for (const src of m.sources) {
          if (src.type === "next-headers") sources.push(src);
          const arg = args[src.index];
          // 文字列（path 形式の引数）は request object の供給源にならない。
          if (!arg || isNullish(arg) || isStringLike(checker.getTypeAtLocation(arg))) continue;
          if (src.type === "param") {
            const f = collectFacts(arg);
            for (const p of f.params) if (p.fn === w.fn) sources.push({ type: "param", index: p.index, name: p.name });
            for (const o of f.optionProps)
              if (o.fn === w.fn) sources.push({ type: "option", index: o.index, prop: o.prop });
          } else if (src.type === "option") {
            const obj = resolveObjectLiteral(arg);
            const val = obj && findProp(obj, src.prop);
            const f = collectFacts(val ?? arg);
            for (const p of f.params) {
              if (p.fn !== w.fn) continue;
              sources.push(
                val
                  ? { type: "param", index: p.index, name: p.name }
                  : { type: "option", index: p.index, prop: src.prop },
              );
            }
          }
        }
        for (const v of m.auth.headerNames) auth.headerNames.add(v);
        for (const v of m.auth.gates) auth.gates.add(v);
        for (const i of m.auth.sourceParams) {
          const arg = args[i];
          if (!arg) continue;
          for (const p of collectFacts(arg).params) if (p.fn === w.fn) auth.sourceParams.add(p.index);
        }
      }
    }
    const baseList = [...bases];
    const base =
      baseList.length === 1
        ? baseList[0]
        : baseList.includes("backend") && baseList.every((b) => b === "backend" || b === "backend-or-internal")
          ? "backend-or-internal"
          : baseList.length
            ? `mixed(${sorted(bases).join("|")})`
            : "unresolved";
    const prefix = prefixes.size === 1 ? [...prefixes][0] : "";
    w.model = {
      base,
      prefix,
      sources: dedupeSources(sources),
      helper,
      auth,
      evidence,
      finalSinks: [...new Set(finalSinks)],
    };
    modelInProgress.delete(w.fn);
    return w.model;
  }
  for (const w of wrappers.values()) modelOf(w);

  // ---- classification helpers -------------------------------------------
  function identityOfExpr(expr, contextLabels) {
    if (!expr || isNullish(expr)) return { identity: "absent", detail: "no request object supplied" };
    const f = collectFacts(expr);
    if (f.nextHeaders) return { identity: "direct", detail: "page request headers via next/headers headers()" };
    const routeParam = f.params.find((p) => isRouteHandlerExport(p.fn));
    if (routeParam)
      return {
        identity: "direct",
        detail: `incoming Route Handler request '${routeParam.name}' of ${functionName(routeParam.fn)}`,
      };
    const other = f.params[0];
    if (other) {
      const callers = productionCallers(other.fn);
      const callerIds = callers.map((c) => {
        const a = c.arguments[other.index];
        return a ? identityOfExpr(a, contextLabels) : { identity: "absent", detail: "argument omitted" };
      });
      const optional = other.optional ? "; parameter is optional (signing skipped when omitted)" : "";
      if (callers.length && callerIds.every((x) => x.identity === "direct")) {
        return {
          identity: "forwarded",
          detail: `parameter '${other.name}' of ${functionName(other.fn)}; all ${callers.length} production caller(s) pass the incoming request${optional}`,
        };
      }
      if (!callers.length)
        return {
          identity: "unknown",
          detail: `parameter '${other.name}' of ${functionName(other.fn)} with no production caller${optional}`,
        };
      return {
        identity: "forwarded",
        detail: `parameter '${other.name}' of ${functionName(other.fn)}; caller identities: ${callerIds.map((x) => x.identity).join(", ")}${optional}`,
      };
    }
    return { identity: "unknown", detail: `identity source not statically resolvable: ${shortText(expr, 60)}` };
  }

  function evaluateSigningAtCall(w, call, r) {
    const m = w.model;
    if (!m.helper)
      return {
        hmac: "unsigned",
        identity: "absent",
        detail: `${w.name} has no ${SIGNING_HELPER} on its path to the network sink`,
      };
    const args = argsOf(call, r);
    const signed = [];
    const unresolved = [];
    for (const src of m.sources) {
      if (src.type === "next-headers") {
        signed.push({ identity: "direct", detail: "page request headers via next/headers headers()" });
        continue;
      }
      const arg = args[src.index];
      if (!arg) continue;
      if (src.type === "param") {
        if (isNullish(arg) || isStringLike(checker.getTypeAtLocation(arg))) continue;
        signed.push({ ...identityOfExpr(arg), via: `argument ${src.index}` });
      } else {
        const obj = resolveObjectLiteral(arg);
        if (!obj) {
          if (!isStringLike(checker.getTypeAtLocation(arg)))
            unresolved.push(`options argument ${src.index} is not a static object literal`);
          continue;
        }
        const val = findProp(obj, src.prop);
        if (val) signed.push({ ...identityOfExpr(val), via: `option '${src.prop}'` });
        else if (hasSpread(obj)) unresolved.push(`option '${src.prop}' may come from a spread`);
      }
    }
    if (signed.length) {
      const best =
        signed.find((s) => s.identity === "direct") ?? signed.find((s) => s.identity === "forwarded") ?? signed[0];
      return { hmac: "conditionally signed", identity: best.identity, detail: `${best.via}: ${best.detail}` };
    }
    if (unresolved.length) return { hmac: "unresolved", identity: "unknown", detail: unresolved.join("; ") };
    if (!m.sources.length)
      return {
        hmac: "unresolved",
        identity: "unknown",
        detail: `${w.name} calls ${SIGNING_HELPER} but its request source could not be mapped to a parameter`,
      };
    return {
      hmac: "unsigned",
      identity: "absent",
      detail: `no request object passed to ${w.name} (identity sources: ${m.sources.map(describeSource).join(", ")})`,
    };
  }

  function describeSource(s) {
    if (s.type === "param") return `param#${s.index}(${s.name})`;
    if (s.type === "option") return `param#${s.index}.${s.prop}`;
    return s.type;
  }

  function authAtWrapperCall(w, call, r) {
    const m = w.model;
    const args = argsOf(call, r);
    const fromRequest = [...m.auth.sourceParams].some(
      (i) => args[i] && !isNullish(args[i]) && !isStringLike(checker.getTypeAtLocation(args[i])),
    );
    let gatedOff = false;
    for (const a of args) {
      const obj = resolveObjectLiteral(a);
      if (!obj) continue;
      for (const g of m.auth.gates) {
        const v = findProp(obj, g);
        if (v && unwrap(v).kind === ts.SyntaxKind.FalseKeyword) gatedOff = true;
      }
    }
    if (!fromRequest)
      return "none forwarded (no incoming request passed; anonymous to Backend unless init headers add credentials)";
    if (gatedOff) return `anonymous: user credentials not forwarded (${[...m.auth.gates].join("/")}: false)`;
    const names = sorted(m.auth.headerNames);
    return `user credentials forwarded from incoming request when present (${names.join(", ") || "headers"})${m.auth.gates.size ? `; gate ${[...m.auth.gates].join("/")} default on` : ""}`;
  }

  function authOfSink(item, contextLabels) {
    const f = item.initExpr ? collectFacts(item.initExpr) : newFacts();
    const keys = [...f.objectKeys].filter((k) => AUTH_HEADER_NAMES.has(k));
    let credentials = null;
    const obj = item.initExpr && resolveObjectLiteral(item.initExpr);
    const cred = obj && findProp(obj, "credentials");
    if (cred) credentials = ts.isStringLiteralLike(unwrap(cred)) ? unwrap(cred).text : "dynamic";
    if (item.r.kind === "axios") {
      const parts = ["axios instance (withCredentials / interceptors not modelled per call)"];
      return parts.join("; ");
    }
    const parts = [];
    if (keys.length) parts.push(`headers: ${sorted(new Set(keys)).join(", ")}`);
    if (credentials) parts.push(`credentials: ${credentials}`);
    const body = obj && findProp(obj, "body");
    if (body) {
      const names = collectFacts(body)
        .params.map((p) => p.name)
        .filter((n) => /refresh|token|password/i.test(n));
      if (names.length) parts.push(`credential material in body (${[...new Set(names)].join(", ")})`);
    }
    const isClient = contextLabels.includes("client");
    if (!parts.length) {
      if (isClient && item.url.category === "relative")
        return "browser same-origin cookies (fetch default credentials)";
      return "none (no Authorization / Cookie forwarded)";
    }
    return parts.join("; ");
  }

  // ---- route table -------------------------------------------------------
  const routes = [];
  for (const [sf, info] of moduleInfo) {
    if (!info.isRoute || info.scope !== "production") continue;
    const routePath = `/${info.rel.replace(/^app\//, "").replace(/\/?route\.(ts|tsx)$/, "")}`
      .split("/")
      .filter((seg) => !/^\(.*\)$/.test(seg))
      .join("/");
    const pattern = new RegExp(
      `^${routePath
        .split("/")
        .map((seg) =>
          /^\[\.\.\..+\]$/.test(seg)
            ? ".+"
            : /^\[\[\.\.\..+\]\]$/.test(seg)
              ? ".*"
              : /^\[.+\]$/.test(seg)
                ? "[^/]+"
                : seg.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"),
        )
        .join("/")}/?$`,
    );
    routes.push({
      sf,
      file: `src/${info.rel}`,
      path: routePath || "/",
      pattern,
      rows: [],
      internalCallers: [],
      dormantCallers: [],
    });
  }
  // 静的 segment を動的 segment より優先する（Next.js の解決順と同じ向き）。
  const dynamicSegments = (r) => (r.path.match(/\[/g) ?? []).length;
  const routesBySpecificity = [...routes].sort(
    (a, b) => dynamicSegments(a) - dynamicSegments(b) || b.path.length - a.path.length,
  );
  function matchRoute(staticPath) {
    if (!staticPath || !staticPath.startsWith("/")) return null;
    const noQuery = staticPath.split("?")[0];
    // 末尾の {*} は query 断片（`${qs ? `?${qs}` : ""}`）のことが多いので、外した形でも照合する。
    const candidates = [noQuery.replace(/\{\*\}/g, "x"), noQuery.replace(/\{\*\}$/, "").replace(/\{\*\}/g, "x")];
    for (const p of candidates) {
      const hit = routesBySpecificity.find((r) => r.pattern.test(p));
      if (hit) return hit;
    }
    return null;
  }

  // ---- rows ----------------------------------------------------------------
  const rows = [];
  for (const item of items) {
    const sf = item.node.getSourceFile();
    const info = moduleInfo.get(sf);
    const ctx = siteContext(item.node);
    const position = loc(item.node);
    const via =
      item.kind === "sink"
        ? item.r.kind === "axios"
          ? `axios.${item.r.method}`
          : `${shortText(item.node.expression, 40)}${item.r.alias ? ` (alias of fetch via '${item.r.alias}')` : ""}`
        : wrappers.get(item.wrapperFn).name + (item.r.alias ? ` (via '${item.r.alias}')` : "");
    const calleeName = item.kind === "sink" ? null : wrappers.get(item.wrapperFn).name;
    const reexport = item.kind === "wrapper-call" ? reexportNote(item.node.expression) : null;
    const row = {
      id: "",
      file: position.file,
      line: position.line,
      column: position.column,
      scope: info.scope,
      function: qualifiedName(item.node),
      kind: item.internalTo ? "wrapper-internal" : item.kind === "sink" ? "direct-sink" : "wrapper-call",
      via,
      wrapper: calleeName,
      internalTo: item.internalTo ? functionName(item.internalTo) : null,
      method: "",
      destination: {},
      runtimeContext: ctx.labels.join("+"),
      reachableFromEntrypoint: ctx.reachable,
      functionReferenced: ctx.functionReferenced,
      provenance: "",
      identity: "",
      hmac: "",
      authentication: "",
      downstreamRoute: null,
      evidence: [],
    };
    if (reexport) row.evidence.push(reexport);

    let base = item.url.category;
    let staticPath = item.url.staticPath;
    if (item.kind === "wrapper-call") {
      const w = wrappers.get(item.wrapperFn);
      if (w.model.base !== "parameter") {
        base = w.model.base;
        staticPath = `${w.model.prefix}${staticPath}`.replace(/\/\/+/g, "/");
      }
      row.evidence.push(`wrapper ${w.name} (${w.file}:${w.line}) final sink(s): ${w.model.finalSinks.join(", ")}`);
    }
    if (item.internalTo) base = "parameter";
    row.destination = {
      category: base,
      staticPath,
      expression: item.url.expression,
      envNames: item.url.envNames,
    };

    // method
    if (item.kind === "sink") row.method = methodOf(item.initExpr, item.r);
    else {
      const w = wrappers.get(item.wrapperFn);
      const args = argsOf(item.node, item.r);
      const initArg = args.find(
        (a, i) => i > item.urlArgIndex && resolveObjectLiteral(a) && findProp(resolveObjectLiteral(a), "method"),
      );
      if (initArg) row.method = methodOf(initArg, { kind: "global-fetch" });
      else if (w.name === "bffPostJsonWithAuthFromReq" || /post/i.test(w.name)) row.method = "POST";
      else {
        const req = args.find((a) => !isStringLike(checker.getTypeAtLocation(a)) && !resolveObjectLiteral(a));
        row.method =
          req && w.name === "djFetch" ? "incoming request method (djFetch default)" : "GET (wrapper default)";
      }
    }

    // signing / identity
    const isBackendBound = ["backend", "backend-or-internal"].includes(base);
    const isInternal = ["relative", "internal-bff", "relative-env-overridable"].includes(base);
    if (item.internalTo) {
      row.hmac = "see wrapper call sites";
      row.identity = "see wrapper call sites";
      row.provenance = "see wrapper call sites";
      row.authentication = "see wrapper call sites";
      const w = wrappers.get(item.internalTo);
      row.evidence.push(
        `final network sink of wrapper ${w.name}; URL path comes from its parameter(s) ${sorted(w.urlParamIndices).join(", ")}`,
      );
      row.evidence.push(...w.model.evidence);
    } else {
      let sig;
      if (item.kind === "wrapper-call") {
        sig = evaluateSigningAtCall(wrappers.get(item.wrapperFn), item.node, item.r);
        row.authentication = authAtWrapperCall(wrappers.get(item.wrapperFn), item.node, item.r);
      } else {
        const initFacts = item.initExpr ? collectFacts(item.initExpr) : newFacts();
        const signing = [
          ...initFacts.signingCalls.map((s) => ({ ...s, where: "init" })),
          ...signingCallsInBodies(item.node, topNamedFunction(item.node)),
        ];
        if (signing.length) {
          const s = signing[0];
          const id = identityOfExpr(s.call.arguments[0]);
          sig = {
            hmac: "conditionally signed",
            identity: id.identity,
            detail: `${SIGNING_HELPER} [${s.where}] at ${loc(s.call).file}:${loc(s.call).line}: ${id.detail}`,
          };
          if (initFacts.calls.size && s.where === "init")
            row.evidence.push(`signing helper reached through: ${sorted(initFacts.calls).join(", ")}`);
        } else
          sig = {
            hmac: "unsigned",
            identity: "absent",
            detail: `no ${SIGNING_HELPER} in init expression or enclosing function body`,
          };
        row.authentication = authOfSink(item, ctx.labels);
      }

      if (isBackendBound) {
        row.hmac = sig.hmac;
        row.identity = sig.identity;
        row.evidence.push(sig.detail);
        if (base === "backend-or-internal")
          row.evidence.push(
            "destination depends on env: Backend when a Backend env is set, otherwise the app's own BFF",
          );
      } else if (isInternal || base === "ambiguous-env") {
        row.hmac = "not applicable (non-Backend hop)";
        if (ctx.labels.includes("client") && ctx.labels.length === 1) {
          row.identity = "direct";
          row.evidence.push(
            "browser → BFF: the browser's own connection reaches Vercel; the BFF route decides signing",
          );
        } else if (ctx.labels.length && !ctx.labels.includes("client")) {
          row.identity = "absent";
          row.evidence.push(
            "server → own BFF: the BFF route sees the Vercel function egress, not the browser (docs/audit/ws04 §13.2; inferred, not measured)",
          );
        } else {
          row.identity = "unknown";
        }
        if (sig.hmac === "conditionally signed")
          row.evidence.push(`note: signing helper present but destination is not the Backend (${sig.detail})`);
        if (!ctx.labels.includes("client") && base === "relative") {
          row.evidence.push("relative URL in server code: Node fetch rejects relative URLs at runtime");
        }
      } else if (base === "external") {
        row.hmac = "not applicable (non-Backend hop)";
        row.identity = "absent";
      } else {
        row.hmac = "unresolved";
        row.identity = "unknown";
        row.evidence.push(`destination not statically resolvable (${base}); not assumed safe`);
        if (sig.hmac === "conditionally signed") row.evidence.push(sig.detail);
      }

      if (isInternal || base === "backend-or-internal" || base === "relative-env-overridable") {
        const route = matchRoute(staticPath);
        if (route) {
          row.downstreamRoute = route.path;
          const serverSide = ctx.labels.some((l) => l !== "client" && l !== "unknown");
          if (serverSide && info.scope === "production") {
            if (ctx.reachable)
              route.internalCallers.push(
                `${row.file}:${row.line}${ctx.labels.includes("client") ? " (shared client/server module)" : ""}`,
              );
            else route.dormantCallers.push(`${row.file}:${row.line}`);
          }
        } else if (staticPath.startsWith("/api")) {
          row.downstreamRoute = "(no matching Route Handler)";
        }
      }
    }

    // provenance（後で route の internal caller を見て確定）
    row._item = item;
    rows.push(row);
  }

  function reexportNote(calleeExpr) {
    const e = unwrap(calleeExpr);
    const target = ts.isPropertyAccessExpression(e) ? e.name : e;
    let s = checker.getSymbolAtLocation(target);
    const hops = [];
    let guard = 0;
    while (s && s.flags & ts.SymbolFlags.Alias && guard++ < 10) {
      const d = s.declarations?.[0];
      if (d) hops.push(`${loc(d).file}:${loc(d).line}`);
      s = checker.getImmediateAliasedSymbol(s);
    }
    return hops.length > 1 ? `resolved through ${hops.length} import/re-export hop(s): ${hops.join(" → ")}` : null;
  }

  // route ごとに backend 行を集計
  for (const row of rows) {
    if (row.scope !== "production") continue;
    const route = routes.find((r) => r.file === row.file);
    if (route && row.kind !== "wrapper-internal") route.rows.push(row);
  }
  // wrapper 内部 helper（route 外 module）の呼び出しを route に紐付ける: route file 内の wrapper-call 行で足りる。

  for (const row of rows) {
    const labels = row.runtimeContext.split("+");
    if (row.kind === "wrapper-internal") continue;
    if (labels.length === 1 && labels[0] === "client") row.provenance = "original user request";
    else if (labels.every((l) => l === "ssr" || l === "server-action"))
      row.provenance = "original user request (server render / action)";
    else if (labels.includes("route-handler") && labels.length === 1) {
      const route = routes.find((r) => r.file === row.file);
      if (route && route.internalCallers.length)
        row.provenance = "original or internal (route also called by server-side fetch)";
      else if (route) row.provenance = "original user request";
      else row.provenance = "original or internal (shared server module reached from Route Handlers)";
    } else if (!row.reachableFromEntrypoint)
      row.provenance = "unknown (module not reachable from a Next.js entrypoint)";
    else row.provenance = "unknown (mixed contexts)";
  }

  // downstream route の集計を internal 行へ
  for (const row of rows) {
    if (!row.downstreamRoute || row.downstreamRoute.startsWith("(")) continue;
    const route = routes.find((r) => r.path === row.downstreamRoute);
    const classes = new Set(
      route.rows.filter((r) => ["backend", "backend-or-internal"].includes(r.destination.category)).map((r) => r.hmac),
    );
    row.downstreamHmac = classes.size ? sorted(classes).join(" / ") : "route makes no Backend call";
  }

  // ---- unresolved dynamic calls ------------------------------------------
  const unresolved = [];
  const networkReturn = /\b(Response|NextResponse|AxiosResponse)\b/;
  for (const c of allCalls) {
    if (c.r.kind !== "dynamic") continue;
    let ret;
    try {
      const sig = checker.getResolvedSignature(c.node);
      ret = sig ? checker.typeToString(checker.getReturnTypeOfSignature(sig)) : "";
    } catch {
      ret = "";
    }
    const calleeText = shortText(c.node.expression, 60);
    const looksNetwork = networkReturn.test(ret) || /fetch|axios|request|http/i.test(calleeText);
    if (!looksNetwork) continue;
    const position = loc(c.node);
    unresolved.push({
      file: position.file,
      line: position.line,
      scope: moduleInfo.get(c.sf).scope,
      function: qualifiedName(c.node),
      callee: calleeText,
      reason: c.r.reason,
      returnType: ret || "(unknown)",
    });
  }
  for (const ref of escapedRefs) {
    const position = loc(ref.node);
    unresolved.push({
      file: position.file,
      line: position.line,
      scope: moduleInfo.get(ref.sf).scope,
      function: qualifiedName(ref.node),
      callee: shortText(ref.node.parent, 60),
      reason: "global fetch referenced as a value (escapes static call tracking)",
      returnType: "(n/a)",
    });
  }
  for (const w of wrappers.values()) {
    for (const ref of escapedFunctionRefs(w.fn)) {
      const position = loc(ref);
      unresolved.push({
        file: position.file,
        line: position.line,
        scope: moduleInfo.get(ref.getSourceFile()).scope,
        function: qualifiedName(ref),
        callee: shortText(ref.parent, 60),
        reason: `wrapper ${w.name} referenced as a value (call sites through this reference are not tracked)`,
        returnType: "(n/a)",
      });
    }
  }
  for (const row of rows) {
    if (row.hmac === "unresolved" && row.kind !== "wrapper-internal") {
      unresolved.push({
        file: row.file,
        line: row.line,
        scope: row.scope,
        function: row.function,
        callee: row.via,
        reason: `destination category '${row.destination.category}' (${row.destination.expression})`,
        returnType: "(request site)",
      });
    }
  }
  unresolved.sort((a, b) => (a.file === b.file ? a.line - b.line : a.file < b.file ? -1 : 1));

  rows.sort((a, b) => (a.file === b.file ? a.line - b.line || a.column - b.column : a.file < b.file ? -1 : 1));
  rows.forEach((r, i) => {
    r.id = `R${String(i + 1).padStart(3, "0")}`;
    delete r._item;
  });

  const wrapperList = [...wrappers.values()]
    .map((w) => ({
      name: w.name,
      file: w.file,
      line: w.line,
      known: KNOWN_WRAPPERS.includes(w.name),
      urlParamIndices: sorted(w.urlParamIndices).map(Number),
      base: w.model.base,
      signingHelperOnPath: w.model.helper,
      identitySources: w.model.sources.map(describeSource),
      authHeaders: sorted(w.model.auth.headerNames),
      authSourceParams: sorted(w.model.auth.sourceParams).map(Number),
      authGates: sorted(w.model.auth.gates),
      finalSinks: w.model.finalSinks,
      productionCallSites: productionCallers(w.fn).length,
      allCallSites: (callsByFn.get(w.fn) ?? []).length,
      evidence: w.model.evidence,
    }))
    .sort((a, b) => (a.file === b.file ? a.line - b.line : a.file < b.file ? -1 : 1));

  const routeList = routes
    .map((r) => {
      const backendRows = r.rows.filter((x) => ["backend", "backend-or-internal"].includes(x.destination.category));
      return {
        path: r.path,
        file: r.file,
        backendCalls: backendRows.length,
        hmac: sorted(new Set(backendRows.map((x) => x.hmac))),
        internalServerCallers: [...new Set(r.internalCallers)].sort(),
        dormantServerCallers: [...new Set(r.dormantCallers)].sort(),
      };
    })
    .sort((a, b) => (a.path < b.path ? -1 : 1));

  return {
    files: sourceFiles.map((sf) => ({
      file: `src/${rel(sf)}`,
      scope: moduleInfo.get(sf).scope,
      context: contextOf(sf).labels.join("+"),
      reachable: contextOf(sf).reachable,
    })),
    rows,
    wrappers: wrapperList,
    routes: routeList,
    unresolved,
    sources: new Map(sourceFiles.map((sf) => [`src/${rel(sf)}`, sf])),
    signingCallSites: allCalls
      .filter((c) => c.r.kind === "project-fn" && c.r.name === SIGNING_HELPER)
      .map((c) => ({ ...loc(c.node), scope: moduleInfo.get(c.sf).scope })),
    callAnchors: buildCallAnchors(allCalls, loc, items),
  };
}

function buildCallAnchors(allCalls, loc, items) {
  // reconciliation 用: AST が見た call の callee 内 identifier の位置（file:line:col → 分類）
  const itemNodes = new Set(items.map((i) => i.node));
  const anchors = new Map();
  for (const c of allCalls) {
    const ids = [];
    const visit = (n) => {
      if (ts.isIdentifier(n)) ids.push(n);
      ts.forEachChild(n, visit);
    };
    visit(c.node.expression);
    const cls = itemNodes.has(c.node)
      ? "request-site"
      : c.r.kind === "project-fn"
        ? `project-fn:${c.r.name}`
        : c.r.kind === "dynamic"
          ? "dynamic"
          : `other:${c.r.name ?? c.r.kind}`;
    for (const id of ids) {
      const p = loc(id);
      anchors.set(`${p.file}:${p.line}:${p.column}`, cls);
    }
  }
  return anchors;
}

// ---------------------------------------------------------------------------
// Independent text search and reconciliation
// ---------------------------------------------------------------------------

export const TEXT_PATTERNS = Object.freeze([
  { id: "fetch", re: /\bfetch\s*\(/g, anchor: "fetch" },
  { id: "djFetch", re: /\bdjFetch\s*\(/g, anchor: "djFetch" },
  { id: "bffFetchWithAuthFromReq", re: /\bbffFetchWithAuthFromReq\s*\(/g, anchor: "bffFetchWithAuthFromReq" },
  { id: "bffPostJsonWithAuthFromReq", re: /\bbffPostJsonWithAuthFromReq\s*\(/g, anchor: "bffPostJsonWithAuthFromReq" },
  { id: "clientIdentityHeaders", re: /\bclientIdentityHeaders\s*\(/g, anchor: "clientIdentityHeaders" },
  {
    id: "axios-method",
    re: /\b(axios|api)\s*\.\s*(request|get|delete|head|options|post|put|patch|postForm|putForm|patchForm)\s*(<[^>(]*>)?\s*\(/g,
    anchor: null,
  },
  {
    id: "backend-origin-reference",
    re: /\b(getDjangoOrigin|DJANGO_ORIGIN|BACKEND_ORIGIN|DJANGO_API_BASE_URL|BACKEND_BASE_URL|BACKEND_URL)\b/g,
    anchor: null,
  },
]);

function commentAndStringRanges(sf) {
  const ranges = [];
  const scanner = ts.createScanner(ts.ScriptTarget.Latest, false, sf.languageVariant, sf.text);
  // コメントは trivia として scan する。文字列 literal は AST から取る（template の誤認を避けるため）。
  let kind = scanner.scan();
  while (kind !== ts.SyntaxKind.EndOfFileToken) {
    if (kind === ts.SyntaxKind.SingleLineCommentTrivia || kind === ts.SyntaxKind.MultiLineCommentTrivia) {
      ranges.push({ start: scanner.getTokenPos(), end: scanner.getTextPos(), type: "comment" });
    }
    kind = scanner.scan();
  }
  const visit = (n) => {
    if (
      ts.isStringLiteral(n) ||
      ts.isNoSubstitutionTemplateLiteral(n) ||
      ts.isTemplateHead(n) ||
      ts.isTemplateMiddle(n) ||
      ts.isTemplateTail(n) ||
      ts.isRegularExpressionLiteral(n)
    ) {
      ranges.push({ start: n.getStart(sf), end: n.getEnd(), type: "string" });
    }
    if (ts.isJsxText(n)) ranges.push({ start: n.getStart(sf), end: n.getEnd(), type: "string" });
    ts.forEachChild(n, visit);
  };
  visit(sf);
  return ranges;
}

function declarationKindAt(sf, pos) {
  let found = null;
  const visit = (n) => {
    if (found || pos < n.getFullStart() || pos >= n.getEnd()) return;
    if (ts.isIdentifier(n) && n.getStart(sf) === pos) {
      found = n;
      return;
    }
    ts.forEachChild(n, visit);
  };
  visit(sf);
  if (!found) return null;
  const p = found.parent;
  if (
    (ts.isFunctionDeclaration(p) ||
      ts.isMethodDeclaration(p) ||
      ts.isVariableDeclaration(p) ||
      ts.isMethodSignature(p) ||
      ts.isPropertySignature(p) ||
      ts.isPropertyAssignment(p) ||
      ts.isParameter(p)) &&
    p.name === found
  ) {
    return "declaration";
  }
  if (ts.isImportSpecifier(p) || ts.isExportSpecifier(p) || ts.isImportClause(p) || ts.isNamespaceImport(p))
    return "import/export";
  return "reference";
}

export function reconcile(result) {
  const out = [];
  const astRequestSites = new Set(result.rows.map((r) => `${r.file}:${r.line}`));
  const known = new Set(TEXT_PATTERNS.map((p) => p.anchor).filter(Boolean));
  const wrapperPatterns = result.wrappers
    .filter((w) => !known.has(w.name) && /^[A-Za-z_$][\w$]*$/.test(w.name))
    .map((w) => ({
      id: `wrapper:${w.name}`,
      re: new RegExp(`\\b${escapeRegExp(w.name)}\\s*(<[^>(]*>)?\\s*\\(`, "g"),
      anchor: w.name,
    }));
  for (const pattern of [...TEXT_PATTERNS, ...wrapperPatterns]) {
    const summary = { pattern: pattern.id, textHits: 0, byClass: {}, unexplained: [] };
    for (const [file, sf] of result.sources) {
      const text = sf.text;
      const ranges = commentAndStringRanges(sf);
      const re = new RegExp(pattern.re.source, "g");
      let m;
      while ((m = re.exec(text))) {
        summary.textHits += 1;
        const anchorOffset = pattern.anchor ? m.index + m[0].indexOf(pattern.anchor) : m.index;
        const { line, character } = sf.getLineAndCharacterOfPosition(anchorOffset);
        const key = `${file}:${line + 1}:${character + 1}`;
        let cls;
        const inRange = ranges.find((r) => anchorOffset >= r.start && anchorOffset < r.end);
        if (inRange) cls = inRange.type === "comment" ? "comment" : "string/regex literal";
        else if (result.callAnchors.has(key)) {
          const a = result.callAnchors.get(key);
          cls = a === "request-site" ? "AST request site" : `AST call (${a.replace(/:.*$/, "")})`;
        } else if (pattern.anchor === null && pattern.id === "axios-method") {
          const sub = new RegExp(
            /\.\s*(request|get|delete|head|options|post|put|patch|postForm|putForm|patchForm)\b/.source,
          ).exec(m[0]);
          const methodOffset = m.index + (sub ? sub.index + sub[0].indexOf(sub[1]) : 0);
          const mp = sf.getLineAndCharacterOfPosition(methodOffset);
          const k2 = `${file}:${mp.line + 1}:${mp.character + 1}`;
          const a = result.callAnchors.get(k2);
          cls = a === "request-site" ? "AST request site" : a ? `AST call (${a.replace(/:.*$/, "")})` : null;
        } else {
          const dk = declarationKindAt(sf, anchorOffset);
          if (dk === "declaration" || dk === "import/export") cls = dk;
          else if (pattern.id === "backend-origin-reference") {
            cls = astRequestSites.has(`${file}:${line + 1}`)
              ? "AST request site (same line)"
              : "backend-origin reference (URL/env construction; see row evidence)";
          }
        }
        if (!cls) {
          cls = "unexplained";
          summary.unexplained.push(`${key} ${text.slice(m.index, m.index + 60).split("\n")[0]}`);
        }
        summary.byClass[cls] = (summary.byClass[cls] ?? 0) + 1;
      }
    }
    out.push(summary);
  }
  // AST にあって text に無い（別名経由など）request site
  const textFetchLines = new Set();
  for (const [file, sf] of result.sources) {
    const names = ["fetch", ...known, ...result.wrappers.map((w) => w.name)]
      .filter((n) => /^[A-Za-z_$][\w$]*$/.test(n))
      .map(escapeRegExp);
    const re = new RegExp(
      `\\b(${[...new Set(names)].join("|")})\\s*(<[^>(]*>)?\\s*\\(|\\.\\s*(request|get|delete|head|options|post|put|patch|postForm|putForm|patchForm)\\s*(<[^>(]*>)?\\s*\\(`,
      "g",
    );
    let m;
    while ((m = re.exec(sf.text))) textFetchLines.add(`${file}:${sf.getLineAndCharacterOfPosition(m.index).line + 1}`);
  }
  const astOnly = result.rows
    .filter((r) => !textFetchLines.has(`${r.file}:${r.line}`))
    .map((r) => `${r.id} ${r.file}:${r.line} ${r.via}`);
  // production の署名 helper 呼び出しが、どれかの request site / wrapper の根拠に紐付いているか
  const evidenceText = [...result.rows.flatMap((r) => r.evidence), ...result.wrappers.flatMap((w) => w.evidence)].join(
    "\n",
  );
  const orphanSigningCalls = result.signingCallSites
    .filter((s) => s.scope === "production" && !evidenceText.includes(`${s.file}:${s.line}`))
    .map((s) => `${s.file}:${s.line}`);
  const unexplainedTotal = out.reduce((n, s) => n + s.unexplained.length, 0) + orphanSigningCalls.length;
  return {
    patterns: out,
    astOnlyRequestSites: astOnly,
    orphanSigningCalls,
    unexplainedTotal,
    status: unexplainedTotal === 0 ? "RECONCILED" : "NOT RECONCILED",
  };
}

// ---------------------------------------------------------------------------
// Report
// ---------------------------------------------------------------------------

export function summarize(result, reconciliation) {
  const prod = result.rows.filter((r) => r.scope === "production");
  const count = (rows, key) => rows.reduce((acc, r) => ((acc[key(r)] = (acc[key(r)] ?? 0) + 1), acc), {});
  const requestRows = prod.filter((r) => r.kind !== "wrapper-internal");
  const backendRows = requestRows.filter((r) => ["backend", "backend-or-internal"].includes(r.destination.category));
  return {
    filesAnalyzed: result.files.length,
    filesByScope: count(result.files, (f) => f.scope),
    productionRows: prod.length,
    rowsByKind: count(prod, (r) => r.kind),
    requestSitesByDestination: count(requestRows, (r) => r.destination.category),
    backendSitesByHmac: count(backendRows, (r) => r.hmac),
    backendSitesByIdentity: count(backendRows, (r) => r.identity),
    requestSitesByContext: count(requestRows, (r) => r.runtimeContext),
    testAndStoryRows: result.rows.length - prod.length,
    wrappers: result.wrappers.length,
    unresolvedProduction: result.unresolved.filter((u) => u.scope === "production").length,
    unresolvedTest: result.unresolved.filter((u) => u.scope !== "production").length,
    reconciliation: reconciliation ? reconciliation.status : "not run",
  };
}

/** RegExp の特殊文字（backslash を含む）をすべて escape する。 */
export function escapeRegExp(s) {
  return String(s).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/** Markdown table cell 用。backslash を先に escape しないと `\|` が列区切りとして解釈される。 */
export function mdEscape(s) {
  return String(s ?? "")
    .replace(/\\/g, "\\\\")
    .replace(/\|/g, "\\|")
    .replace(/\n/g, " ");
}

export function renderMarkdown(result, reconciliation) {
  const s = summarize(result, reconciliation);
  const lines = [];
  lines.push("# BFF Backend call-graph inventory（generated）");
  lines.push("");
  lines.push("Generated by `apps/web/scripts/audit/bff-backend-call-graph.mjs`. Do not edit by hand; regenerate with");
  lines.push(
    "`pnpm -C apps/web audit:bff-identity`. Interpretation and caveats: `bff-anonymous-identity-paths-audit-2026-10-26.md`.",
  );
  lines.push("");
  lines.push("## Summary");
  lines.push("");
  lines.push("```text");
  lines.push(JSON.stringify(s, null, 2));
  lines.push("```");
  lines.push("");
  lines.push("## Wrappers（URL taken from a parameter; traced to the final sink）");
  lines.push("");
  lines.push(
    "| wrapper | defined | URL param | base | signing helper on path | identity sources | auth headers / gates | prod call sites | final sink(s) |",
  );
  lines.push("| --- | --- | --- | --- | --- | --- | --- | --- | --- |");
  for (const w of result.wrappers) {
    lines.push(
      `| ${mdEscape(w.name)}${w.known ? "（known）" : ""} | ${w.file}:${w.line} | ${w.urlParamIndices.join(", ")} | ${w.base} | ${w.signingHelperOnPath ? "yes" : "no"} | ${mdEscape(w.identitySources.join(", ") || "—")} | ${mdEscape([...w.authHeaders, ...w.authGates.map((g) => `gate:${g}`)].join(", ") || "—")} | ${w.productionCallSites} | ${mdEscape(w.finalSinks.join(", "))} |`,
    );
  }
  lines.push("");
  lines.push("## Route Handlers → Backend");
  lines.push("");
  lines.push(
    "| route | file | Backend calls | HMAC | server-side internal callers（reachable） | unreferenced server-side callers |",
  );
  lines.push("| --- | --- | --- | --- | --- | --- |");
  for (const r of result.routes) {
    lines.push(
      `| ${mdEscape(r.path)} | ${r.file} | ${r.backendCalls} | ${mdEscape(r.hmac.join(" / ") || "—")} | ${mdEscape(r.internalServerCallers.join(", ") || "—")} | ${mdEscape(r.dormantServerCallers.join(", ") || "—")} |`,
    );
  }
  lines.push("");
  lines.push("## Per-call-site inventory（production scope）");
  lines.push("");
  lines.push(
    "| id | site | function | kind / via | method | destination | context | provenance | identity | HMAC | auth | evidence |",
  );
  lines.push("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |");
  for (const r of result.rows.filter((x) => x.scope === "production")) {
    const dest = `${r.destination.category}: \`${mdEscape(r.destination.staticPath || "—")}\`${r.destination.envNames.length ? ` env[${r.destination.envNames.join(",")}]` : ""}${r.downstreamRoute ? ` → route ${mdEscape(r.downstreamRoute)}${r.downstreamHmac ? ` (${mdEscape(r.downstreamHmac)})` : ""}` : ""}`;
    lines.push(
      `| ${r.id} | ${r.file}:${r.line} | ${mdEscape(r.function)} | ${r.kind} / ${mdEscape(r.via)} | ${mdEscape(r.method)} | ${dest} | ${r.runtimeContext}${r.functionReferenced === false ? " (function unreferenced)" : r.reachableFromEntrypoint ? "" : " (module unreferenced)"} | ${mdEscape(r.provenance)} | ${r.identity} | ${r.hmac} | ${mdEscape(r.authentication)} | ${mdEscape(r.evidence.join("; "))} |`,
    );
  }
  lines.push("");
  lines.push("## Unresolved / dynamic call sites");
  lines.push("");
  lines.push("| site | scope | function | callee | reason | return type |");
  lines.push("| --- | --- | --- | --- | --- | --- |");
  for (const u of result.unresolved) {
    lines.push(
      `| ${u.file}:${u.line} | ${u.scope} | ${mdEscape(u.function)} | \`${mdEscape(u.callee)}\` | ${mdEscape(u.reason)} | ${mdEscape(u.returnType)} |`,
    );
  }
  if (reconciliation) {
    lines.push("");
    lines.push("## Text-search reconciliation");
    lines.push("");
    lines.push(`Status: **${reconciliation.status}**（unexplained text hits: ${reconciliation.unexplainedTotal}）`);
    lines.push("");
    lines.push("| pattern | text hits | classification |");
    lines.push("| --- | --- | --- |");
    for (const p of reconciliation.patterns) {
      lines.push(
        `| ${p.pattern} | ${p.textHits} | ${mdEscape(
          Object.entries(p.byClass)
            .sort()
            .map(([k, v]) => `${k}: ${v}`)
            .join("; "),
        )} |`,
      );
    }
    lines.push("");
    lines.push(
      `AST request sites without a matching text hit on the same line（alias / multi-line）: ${reconciliation.astOnlyRequestSites.length}`,
    );
    for (const a of reconciliation.astOnlyRequestSites) lines.push(`- ${a}`);
    lines.push("");
    lines.push(
      `Production \`${SIGNING_HELPER}\` calls not attributed to any request site or wrapper: ${reconciliation.orphanSigningCalls.length}`,
    );
    for (const o of reconciliation.orphanSigningCalls) lines.push(`- ${o}`);
    for (const p of reconciliation.patterns)
      for (const u of p.unexplained) lines.push(`- unexplained ${p.pattern}: ${u}`);
  }
  lines.push("");
  lines.push("## Test / Storybook scope rows");
  lines.push("");
  lines.push(
    `${result.rows.length - result.rows.filter((x) => x.scope === "production").length} rows in test or Storybook files are excluded from the inventory above and listed in the JSON output.`,
  );
  lines.push("");
  return lines.join("\n");
}

export function toJson(result, reconciliation) {
  return {
    summary: summarize(result, reconciliation),
    wrappers: result.wrappers,
    routes: result.routes,
    rows: result.rows,
    unresolved: result.unresolved,
    reconciliation: reconciliation
      ? {
          status: reconciliation.status,
          unexplainedTotal: reconciliation.unexplainedTotal,
          patterns: reconciliation.patterns,
          astOnlyRequestSites: reconciliation.astOnlyRequestSites,
          orphanSigningCalls: reconciliation.orphanSigningCalls,
        }
      : null,
  };
}

export function runAudit(webRoot) {
  const { program, srcDir } = createProgramFromDisk(webRoot);
  const result = analyzeProgram(program, { srcDir });
  const reconciliation = reconcile(result);
  return { result, reconciliation };
}

// ---------------------------------------------------------------------------
// CLI
// ---------------------------------------------------------------------------

function main(argv) {
  const webRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
  const arg = (name) => {
    const i = argv.indexOf(name);
    return i >= 0 ? argv[i + 1] : null;
  };
  const { result, reconciliation } = runAudit(webRoot);
  const json = `${JSON.stringify(toJson(result, reconciliation), null, 2)}\n`;
  const md = renderMarkdown(result, reconciliation);
  const jsonOut = arg("--json");
  const mdOut = arg("--md");
  const check = arg("--check");
  if (jsonOut) fs.writeFileSync(jsonOut, json);
  if (mdOut) fs.writeFileSync(mdOut, md);
  process.stdout.write(`${JSON.stringify(summarize(result, reconciliation), null, 2)}\n`);
  if (check) {
    const existing = fs.readFileSync(check, "utf8");
    if (existing !== json) {
      process.stderr.write(`inventory drift: ${check} differs from the current analysis; regenerate it\n`);
      return 1;
    }
  }
  return reconciliation.status === "RECONCILED" ? 0 : 2;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  process.exitCode = main(process.argv.slice(2));
}
