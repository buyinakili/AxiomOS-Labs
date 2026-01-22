(define (problem move-report)
  (:domain file-manager)
  (:objects 
    report_pdf - file
    root backup - folder
  )

  (:init
    (at report_pdf root)
    (connected root backup)
  )

  (:goal (and
    (at report_pdf backup)
  ))
)