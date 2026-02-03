(define (problem file-management-problem)
  (:domain file-manager)
  (:objects
    root backup - folder
<<<<<<< HEAD
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
=======
    good.txt good_dot_txt abc_dot_txt - file
  )
  (:init
    (= (total-cost) 0)
    (at good.txt backup)
    (at good_dot_txt backup)
    (connected backup root)
    (connected root backup)
    (scanned backup)
    (scanned root)
  )
  (:goal (and (not (at good.txt root)) (not (at abc_dot_txt root)) (not (at good.txt backup))))
>>>>>>> 9d71f6d (发现llm生成的goal有很低概率由于幻觉不遵循转义原则，添加了对goal的检验，若出现未转义的目标，会自动转义)
  (:metric minimize (total-cost))
)