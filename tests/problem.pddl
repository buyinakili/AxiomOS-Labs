(define (problem file-management-problem)
  (:domain file-manager)
  (:objects
    root - folder
    txt_dot_txt new_dot_txt abc_dot_txt - file
  )
  (:init
    (= (total-cost) 0)
    (at abc_dot_txt root)
    (connected root root)
    (scanned root)
  )
  (:goal (and (not (at txt_dot_txt root)) (at new_dot_txt root)))
  (:metric minimize (total-cost))
)