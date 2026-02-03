(define (problem file-management-problem)
  (:domain file-manager)
  (:objects
    root backup - folder
    good_dot_txt abc_dot_txt - file
  )
  (:init
    (= (total-cost) 0)
    (connected backup root)
    (connected root backup)
    (scanned backup)
    (scanned root)
  )
  (:goal (and (not (at good_dot_txt backup)) (not (at abc_dot_txt root))))
  (:metric minimize (total-cost))
)