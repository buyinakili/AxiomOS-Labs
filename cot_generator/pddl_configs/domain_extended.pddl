(define (domain file-manager-extended)
  (:requirements :strips :typing :action-costs) ; 开启成本需求
  (:types 
    file folder archive name - object
    filename - name  ; 文件名类型
  )

  (:functions 
    (total-cost) - number ; 定义总价值/开销计数器
  )

  (:predicates
    ;; 基础谓词
    (at ?f - file ?d - folder)
    (connected ?d1 ?d2 - folder)
    (has_admin_rights)
    (scanned ?d - folder)
    (is_created ?obj - (either file folder archive))
    (is_compressed ?f - file ?a - archive)
    
    ;; 扩展谓词
    (has_name ?f - file ?n - filename)  ; 文件有名称
    (is_empty ?d - folder)              ; 文件夹为空
    (is_copied ?src - file ?dst - file) ; 文件被复制
  )

  ;; ========== 九大原子动作 ==========

  ;; 1. scan - 扫描文件夹
  (:action scan
    :parameters (?d - folder)
    :precondition (and 
        (has_admin_rights)
    )
    :effect (and 
        (scanned ?d)
        (increase (total-cost) 1)
    )
  )

  ;; 2. move - 移动文件
  (:action move
    :parameters (?f - file ?src - folder ?dst - folder)
    :precondition (and 
        (at ?f ?src) 
        (connected ?src ?dst) 
        (has_admin_rights)
    )
    :effect (and 
        (at ?f ?dst) 
        (not (at ?f ?src))
        (is_created ?f)  ; 确保规划器优先使用
        (increase (total-cost) 1)
    )
  )

  ;; 3. remove - 删除文件
  (:action remove
    :parameters (?f - file ?d - folder)
    :precondition (and 
        (at ?f ?d)
        (has_admin_rights)
    )
    :effect (and 
        (not (at ?f ?d))
        (increase (total-cost) 1)
    )
  )

  ;; 4. rename - 重命名文件
  (:action rename
    :parameters (?f - file ?old_name - filename ?new_name - filename ?d - folder)
    :precondition (and 
        (at ?f ?d)
        (has_name ?f ?old_name)
        (has_admin_rights)
    )
    :effect (and 
        (not (has_name ?f ?old_name))
        (has_name ?f ?new_name)
        (is_created ?f)  ; 确保规划器优先使用
        (increase (total-cost) 1)
    )
  )

  ;; 5. copy - 复制文件
  (:action copy
    :parameters (?src - file ?dst - file ?src_folder - folder ?dst_folder - folder)
    :precondition (and 
        (at ?src ?src_folder)
        (connected ?src_folder ?dst_folder)
        (has_admin_rights)
    )
    :effect (and
        (at ?dst ?dst_folder)
        (is_copied ?src ?dst)
        (is_created ?dst)  ; 确保规划器优先使用
        (increase (total-cost) 2)  ; 复制成本较高
    )
  )

  ;; 6. compress - 压缩文件
  (:action compress
    :parameters (?f - file ?d - folder ?a - archive)
    :precondition (and 
        (at ?f ?d) 
        (has_admin_rights) 
        (scanned ?d)
    )
    :effect (and 
        (is_created ?a) 
        (at ?a ?d) 
        (is_compressed ?f ?a)
        (increase (total-cost) 2)  ; 压缩成本较高
    )
  )

  ;; 7. uncompress - 解压文件
  (:action uncompress
    :parameters (?a - archive ?d - folder ?f - file)
    :precondition (and 
        (at ?a ?d)
        (is_compressed ?f ?a)
        (has_admin_rights)
    )
    :effect (and
        (at ?f ?d)
        (not (is_compressed ?f ?a))  ; 解压后不再压缩
        (is_created ?f)  ; 确保规划器优先使用
        (increase (total-cost) 2)  ; 解压成本较高
    )
  )

  ;; 8. create_file - 创建文件
  (:action create_file
    :parameters (?f - file ?name - filename ?d - folder)
    :precondition (and 
        (has_admin_rights)
        (not (at ?f ?d))  ; 文件不存在
    )
    :effect (and
        (at ?f ?d)
        (has_name ?f ?name)
        (is_created ?f)
        (increase (total-cost) 1)
    )
  )

  ;; 9. create_folder - 创建文件夹
  (:action create_folder
    :parameters (?d - folder ?parent - folder)
    :precondition (and 
        (has_admin_rights)
        (connected ?parent ?d)  ; 父文件夹连接到新文件夹
    )
    :effect (and
        (is_empty ?d)
        (is_created ?d)
        (increase (total-cost) 1)
    )
  )

  ;; ========== 辅助动作 ==========

  ;; get_admin - 获取管理员权限
  (:action get_admin
    :parameters ()
    :effect (and 
        (has_admin_rights)
        (increase (total-cost) 5)  ; 获取权限成本较高
    )
  )

  ;; connect_folders - 连接文件夹（用于建立文件夹关系）
  (:action connect_folders
    :parameters (?d1 ?d2 - folder)
    :precondition (has_admin_rights)
    :effect (and
        (connected ?d1 ?d2)
        (connected ?d2 ?d1)  ; 双向连接
        (increase (total-cost) 1)
    )
  )

)