(define (problem file-management-problem)
  (:domain file-manager)
  (:objects
    root - folder
    abc_dot_txt - file
  )
  (:init
    (= (total-cost) 0)
    (connected root root)
    (scanned root)
  )
  (:goal (and (not (at abc_dot_txt root))))
  (:metric minimize (total-cost))
)