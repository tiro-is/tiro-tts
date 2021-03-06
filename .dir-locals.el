;;; Directory Local Variables
;;; For more information see (info "(emacs) Directory Variables")
((python-mode . ((eval .
                       (add-hook 'before-save-hook
                                 (lambda ()
                                   (when (bound-and-true-p lsp-managed-mode)
                                     (lsp-format-buffer))) 0 t))
                 (eval .
                       (setenv "PYTHONPATH" (s-trim (shell-command-to-string "echo \"import os; print(os.environ['PYTHONPATH'])\" | bazel run //:repl 2>/dev/null"))))
                 (python-shell-interpreter . "bazel")
                 (python-shell-interpreter-args .  "run //:repl -- "))))
