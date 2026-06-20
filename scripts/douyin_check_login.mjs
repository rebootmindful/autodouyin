/**
 * [INPUT]: 依赖 {vendored douyin adapter} 的 {可选短信验证码}
 * [OUTPUT]: 对外提供 {登录状态 JSON}
 * [POS]: {scripts} 的 {Douyin 登录桥接脚本}，把核心 skill 契约接到 vendor adapter
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

import { createDouyinSession, disconnect } from "../adapters/douyin-upload-vendor/src/index.js";

function readSmsCode() {
  const index = process.argv.indexOf("--sms-code");
  return index === -1 ? undefined : process.argv[index + 1];
}

async function main() {
  const smsCode = readSmsCode();
  const { ops } = await createDouyinSession();
  const result = await ops.checkLogin({ smsCode });
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
