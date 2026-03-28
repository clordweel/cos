/** 与 Flutter 壳 [MiniProgramRunnerScreen] 中 WebView User-Agent 约定一致。 */
export function isCosFlutterShell(): boolean {
	if (typeof navigator === "undefined") return false
	return /\bCosWorkApp\b/i.test(navigator.userAgent)
}
