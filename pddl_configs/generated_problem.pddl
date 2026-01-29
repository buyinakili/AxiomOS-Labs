(define (problem delete_txt_file)
  (:domain file-manager)
  (:objects 
    abc_dot_txt - file
    root - folder
  )
  (:init
    (= (total-cost) 0)
    (at abc_dot_txt root)
    (scanned root)
    (connected root root)
  )
  (:goal
    (not (at abc_dot_txt root))
  )
)