#!/bin/bash
ACTION="$1"
FILE_PLAN_COMPLETED="var/plan.completed"
FILE_TASK_FAILED="var/task.failed"
CMD_OPENCODE="proxychains4 -q opencode"

case "$ACTION" in
    "work")
        rm -f $FILE_PLAN_COMPLETED
        while [ ! -f "$FILE_PLAN_COMPLETED" ]; do
            if [ -f "$FILE_TASK_FAILED" ]; then
                echo "[STOP] Task failed. Details from file $FILE_TASK_FAILED:"
                cat "$FILE_TASK_FAILED"
                echo "---"
                echo "[!] Remove the file $FILE_TASK_FAILED when you fix the issue."
                exit 1
            fi
            if $CMD_OPENCODE run "$(cat spec/skills/work.md)" \
                --auto --print-logs --log-level DEBUG 2>&1 \
                | sed -E 's/^timestamp=([^ ]+) /\1: /; s/level=[^ ]+ //; s/run=[^ ]+ //;' \
            ; then
                echo "[OK] Yet another task is processed"
            else
                echo "[ERROR] Yet another task is processed with some error"
            fi
        done
        ;;
    "task")
        $CMD_OPENCODE --agent plan --prompt "$(cat spec/skills/task.md)"
        ;;
    "shell")
        $CMD_OPENCODE --agent plan --prompt "$(cat spec/skills/shell.md)"
        ;;
    *)
        echo "Usage: $0 <work|task|shell>"
        ;;
esac
