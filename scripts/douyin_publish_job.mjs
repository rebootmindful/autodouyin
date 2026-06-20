/**
 * [INPUT]: 依赖 {publish-job.json 与 vendored douyin adapter} 的 {发布任务}
 * [OUTPUT]: 对外提供 {发布结果 JSON}
 * [POS]: {scripts} 的 {Douyin 发布桥接脚本}，把 publish-job 契约接到 vendor adapter
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

import { readFile } from "node:fs/promises";
import { createDouyinSession, disconnect } from "../adapters/douyin-upload-vendor/src/index.js";

function readArg(name) {
  const index = process.argv.indexOf(name);
  return index === -1 ? undefined : process.argv[index + 1];
}

function hasFlag(name) {
  return process.argv.includes(name);
}

async function readJob(path) {
  const text = await readFile(path, "utf8");
  return JSON.parse(text);
}

function ensureJobShape(job) {
  if (job.platform !== "douyin") throw new Error("publish-job platform must be douyin");
  if (!job.video_path) throw new Error("publish-job video_path is required");
  if (!job.title) throw new Error("publish-job title is required");
  if (!job.description) throw new Error("publish-job description is required");
}

async function main() {
  const jobPath = readArg("--job");
  if (!jobPath) throw new Error("need --job <publish-job.json>");
  const timeout = Number(readArg("--timeout") || "300000");
  const prepareOnly = hasFlag("--prepare-only");
  const job = await readJob(jobPath);
  ensureJobShape(job);
  const { ops } = await createDouyinSession();
  const login = await ops.checkLogin();
  if (!login.loggedIn) throw new Error(`not logged in, current phase: ${login.phase}`);
  const result = await ops.publishVideo(job.video_path, {
    title: job.title,
    description: job.description,
    timeout,
    publish: !prepareOnly,
  });
  if (!result.verification?.success) {
    result.warning = "publish click completed, but final success could not be conclusively verified";
  }
  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
}

main()
  .catch((error) => {
    process.stderr.write(`${error.stack || error.message}\n`);
    process.exitCode = 1;
  })
  .finally(() => {
    disconnect();
  });
