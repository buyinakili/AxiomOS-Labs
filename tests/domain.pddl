(define (domain file-manager)
  (:requirements :strips :typing :action-costs) ; 开启成本需求
  (:types file folder archive - object)

  (:functions 
    (total-cost) - number ; 定义总价值/开销计数器
  )

  (:predicates
    (at ?f - file ?d - folder)
    (connected ?d1 ?d2 - folder)
    (has_admin_rights)
    (scanned ?d - folder)
    (is_created ?obj - (either file folder))
    (is_compressed ?f - file ?a - archive)
  )

  ;; --- 基础动作 (Weight: 10) ---
  (:action scan
    :parameters (?d - folder)
    :effect (and 
        (scanned ?d)
    )
  )

  (:action get_admin
    :parameters ()
    :effect (and 
        (has_admin_rights)
        (increase (total-cost) 5)
    )
  )

  ;; --- 物理操作 (Weight: 1) ---
  (:action move
    :parameters (?f - file ?src - folder ?dst - folder)
    :precondition (and (at ?f ?src) (connected ?src ?dst) (has_admin_rights))
    :effect (and 
        (at ?f ?dst) 
        (not (at ?f ?src))
        ;;(increase (total-cost) 1)
        (is_created ?f)
    )
  )

  (:action compress
    :parameters (?f - file ?d - folder ?a - archive)
    :precondition (and (at ?f ?d) (has_admin_rights) (scanned ?d))
    :effect (and 
        (is_created ?a) 
        (at ?a ?d) 
        (is_compressed ?f ?a)
        (increase (total-cost) 1)
    )
  )

  (:action remove_file
    :parameters (?f - file ?d - folder)
    :precondition (and (at ?f ?d))
    :effect (and (not (at ?f ?d))))
  

;; --- AI Generated Action ---
(:action rename_file :parameters (?old_file - file ?new_file - file ?folder - folder) :precondition (and (at ?old_file ?folder) (not (at ?new_file ?folder))) :effect (and (not (at ?old_file ?folder)) (at ?new_file ?folder) (is_created ?new_file)))
)