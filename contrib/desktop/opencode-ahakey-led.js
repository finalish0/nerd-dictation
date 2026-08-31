import { spawn } from "node:child_process"
import fs from "node:fs"
import { homedir } from "node:os"

const AHAKEY = `${homedir()}/git/ahakey-x1/ahakey.sh`
const QUESTION_TOOLS = new Set(["question", "ask_user_question"])
const ND_PID_FILE = `${process.env.XDG_RUNTIME_DIR || `/run/user/${process.getuid()}`}/nerd-dictation.pid`

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function pulse(name) {
  try {
    const child = spawn(AHAKEY, ["pulse", name], {
      detached: true,
      stdio: "ignore",
    })
    child.unref()
  } catch {
    // Pad/daemon optional — never block OpenCode
  }
}

function markTitle() {
  try {
    // So Sway can find this TUI: pad-enter matches title ~ opencode|grok
    process.stdout.write("\x1b]0;opencode\x07")
  } catch {
    // ignore
  }
}

async function suspendDictation() {
  try {
    const pid = parseInt(fs.readFileSync(ND_PID_FILE, "utf8").trim(), 10)
    if (!(pid > 0)) return
    if (!fs.readFileSync(`/proc/${pid}/cmdline`, "utf8").includes("nerd-dictation")) return
    // Freeze immediately, then let the USR1 handler close the mic.
    // 50 ms gaps keep USR1 from racing ahead of SIGSTOP.
    process.kill(pid, "SIGSTOP")
    await sleep(50)
    process.kill(pid, "SIGUSR1")
    await sleep(50)
    process.kill(pid, "SIGCONT")
  } catch {
    // Dictation optional — never block OpenCode
  }
}

export const AhakeyLed = async () => {
  markTitle()
  return {
    "chat.message": async () => {
      markTitle()
      pulse("send")
      await suspendDictation()
      pulse("off")
    },
    "tool.execute.before": async (input) => {
      if (QUESTION_TOOLS.has(input.tool)) pulse("ask")
    },
    "tool.execute.after": async (input) => {
      if (QUESTION_TOOLS.has(input.tool)) pulse("off")
    },
    event: async ({ event }) => {
      switch (event.type) {
        case "session.idle":
          pulse("done")
          break
        case "session.error":
          pulse("error")
          break
        case "permission.asked":
          pulse("ask")
          break
        case "permission.replied":
          pulse("off")
          break
        default:
          break
      }
    },
  }
}
