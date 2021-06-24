;;; Directory Local Variables
;;; For more information see (info "(emacs) Directory Variables")
((python-mode . ((eval .
                       (add-hook 'before-save-hook
                                 (lambda ()
                                   (when (bound-and-true-p lsp-managed-mode)
                                       (lsp-format-buffer))) 0 t)))))
