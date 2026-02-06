(define (problem file-operation-example)
  (:domain file-manager-extended)
  
  (:objects
    root backup - folder
    file1 file2 file3 - file
    archive1 - archive
    name1 name2 name3 - filename
  )
  
  (:init
    ;; 基础连接
    (connected root backup)
    (connected backup root)
    
    ;; 文件位置
    (at file1 root)
    (at file2 root)
    (at file3 backup)
    
    ;; 文件名称
    (has_name file1 name1)
    (has_name file2 name2)
    (has_name file3 name3)
    
    ;; 权限
    (has_admin_rights)
    
    ;; 初始成本
    (= (total-cost) 0)
  )
  
  (:goal (and
    ;; 目标1: file1移动到backup
    (at file1 backup)
    
    ;; 目标2: file2重命名为name3
    (has_name file2 name3)
    
    ;; 目标3: 创建新文件file4
    ;; (需要添加file4对象)
  ))
  
  (:metric minimize (total-cost))
)