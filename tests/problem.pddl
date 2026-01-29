(define (problem file-management-problem)
  (:domain file-manager)
  (:objects
    root backup - folder
    abc_dot_txt - file
  )
  (:init
    (= (total-cost) 0)
    (at abc_dot_txt backup)
    (connected backup root)
    (connected root backup)
    (has_admin_rights)
    (scanned root)
  )
  (:goal (and (at abc_dot_txt backup)))
  (:metric minimize (total-cost))
)