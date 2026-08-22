#!/bin/bash
ACTION="$1"
FILE_PLAN_COMPLETED="var/plan.completed"
FILE_TASK_FAILED="var/task.failed"
CMD_OPENCODE="proxychains4 -q opencode"
WORK_MODEL="zai-coding-plan/glm-5.3"
PLAN_MODEL="zai-coding-plan/glm-5.3"

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
            if $CMD_OPENCODE run "$(cat spec/skill/work.md)" --model "$WORK_MODEL" \
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
        $CMD_OPENCODE --model "$PLAN_MODEL" --agent plan --prompt "$(cat spec/skill/task.md)"
        ;;
    "shell")
        $CMD_OPENCODE --model "$PLAN_MODEL" --agent plan --prompt "$(cat spec/skill/shell.md)"
        ;;
    *)
        echo "Usage: $0 <work|task|shell>"
        ;;
esac
