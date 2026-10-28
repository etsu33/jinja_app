/**
 * @vitest-environment jsdom
 */
// H-2（axios upgrade）: requests go through the real axios pipeline（merge, interceptors, transformRequest,
// error creation）. Only the transport is replaced by a per-request adapter; client code is unchanged.
import { AxiosError, type AxiosAdapter, type InternalAxiosRequestConfig } from "axios";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import api from "../client";
import { apiDelete, apiGet, apiPatchForm, apiPost, isAuthError } from "../http";
import legacyApi from "../../api";

type Captured = InternalAxiosRequestConfig & { url?: string };

function adapter(status = 200, data: unknown = { ok: true }) {
  const calls: Captured[] = [];
  const fn: AxiosAdapter = async (config) => {
    calls.push(config as Captured);
    const response = { data, status, statusText: String(status), headers: {}, config, request: {} };
    if (status >= 400) {
      throw new AxiosError(`Request failed with status code ${status}`, "ERR_BAD_REQUEST", config, {}, response);
    }
    return response;
  };
  return { fn, calls };
}

function header(config: Captured, name: string): unknown {
  const h = config.headers as unknown as { get?: (n: string) => unknown } & Record<string, unknown>;
  return typeof h.get === "function" ? h.get(name) : h[name];
}

function clearCookies() {
  for (const name of ["access_token", "csrftoken"]) document.cookie = `${name}=; Max-Age=0; path=/`;
}

beforeEach(clearCookies);
afterEach(clearCookies);

describe("api client through the real axios pipeline", () => {
  it("GET: /api base, credentials, Bearer from the access_token cookie, no CSRF header", async () => {
    document.cookie = "access_token=tok-123; path=/";
    document.cookie = "csrftoken=csrf-1; path=/";
    const { fn, calls } = adapter(200, { name: "me" });

    await expect(apiGet("/my/profile/", { adapter: fn })).resolves.toEqual({ name: "me" });

    const c = calls[0];
    expect(c.baseURL).toBe("/api");
    expect(c.url).toBe("/my/profile/");
    expect(c.method).toBe("get");
    expect(c.withCredentials).toBe(true);
    expect(header(c, "Authorization")).toBe("Bearer tok-123");
    expect(header(c, "X-CSRFToken")).toBeUndefined();
  });

  it("normalises '/?' before sending, as before", async () => {
    const { fn, calls } = adapter();
    await apiGet("/my/goshuins/?limit=5", { adapter: fn });
    expect(calls[0].url).toBe("/my/goshuins?limit=5");
  });

  it("POST: JSON body, JSON content type, CSRF header from the cookie", async () => {
    document.cookie = "csrftoken=csrf-9; path=/";
    const { fn, calls } = adapter(201, { id: 1 });

    await expect(apiPost("/visits/", { shrine: 7 }, { adapter: fn })).resolves.toEqual({ id: 1 });

    const c = calls[0];
    expect(c.method).toBe("post");
    expect(JSON.parse(String(c.data))).toEqual({ shrine: 7 });
    expect(String(header(c, "Content-Type"))).toContain("application/json");
    expect(header(c, "X-CSRFToken")).toBe("csrf-9");
    expect(header(c, "Authorization")).toBeUndefined();
  });

  it("DELETE carries CSRF; caller headers are merged, not dropped", async () => {
    document.cookie = "csrftoken=csrf-d; path=/";
    const { fn, calls } = adapter(204, "");

    await apiDelete("/favorites/3/", { adapter: fn, headers: { "X-Custom": "1" } });

    expect(header(calls[0], "X-CSRFToken")).toBe("csrf-d");
    expect(header(calls[0], "X-Custom")).toBe("1");
  });

  it("PATCH FormData: the same FormData instance reaches the transport", async () => {
    document.cookie = "csrftoken=csrf-f; path=/";
    const form = new FormData();
    form.append("title", "t");
    const { fn, calls } = adapter(200, { ok: 1 });

    await apiPatchForm("/my/profile/", form, { adapter: fn });

    expect(calls[0].method).toBe("patch");
    expect(calls[0].data).toBe(form);
    expect(header(calls[0], "X-CSRFToken")).toBe("csrf-f");
  });

  it.each([401, 403, 500])("a %s response rejects with an AxiosError carrying the response", async (status) => {
    const { fn } = adapter(status, { detail: "x" });

    const err = await apiGet("/my/profile/", { adapter: fn }).catch((e: unknown) => e);

    expect(err).toBeInstanceOf(AxiosError);
    expect((err as AxiosError).response?.status).toBe(status);
    expect((err as AxiosError).response?.data).toEqual({ detail: "x" });
    expect(isAuthError(err)).toBe(status === 401);
  });

  it("the shared instance keeps its defaults", () => {
    expect(api.defaults.baseURL).toBe("/api");
    expect(api.defaults.withCredentials).toBe(true);
  });
});

describe("legacy lib/api.ts instance", () => {
  it("sends the 15 s timeout and X-Requested-With on every request", async () => {
    const { fn, calls } = adapter();

    await legacyApi.get("/ping/", { adapter: fn });

    expect(calls[0].timeout).toBe(15000);
    expect(calls[0].withCredentials).toBe(true);
    expect(header(calls[0], "X-Requested-With")).toBe("XMLHttpRequest");
  });
});
