(define (problem file-management-problem)
  (:domain file-manager)
  (:objects
    root backup - folder
    abc_dot_txt good_dot_txt - file
  )
  (:init
    (= (total-cost) 0)
    (at abc_dot_txt root)
    (connected backup root)
    (connected root backup)
    (scanned root)
  )
  (:goal (and (at abc_dot_txt backup) (not (at good_dot_txt backup))))
  (:metric minimize (total-cost))
)