# S172 W10 PRE/POST probe+law rows (tb_pre.err / tb_post.err)

## PRE (bin 1f5a524ef59b26fb, MINIANDROID_W10_PROBE=1)
3474:[W10-PROBE] NotificationManager.createNotificationChannel argc=2 status=STUBBED caller=Lcom/fsck/k9/notification/NotificationChannelManager;.$r8$lambda$m3LNel5iYKrrYmwu_gXHemecIYY
3479:[W10-PROBE] NotificationManager.createNotificationChannel argc=2 status=STUBBED caller=Lcom/fsck/k9/notification/NotificationChannelManager;.$r8$lambda$m3LNel5iYKrrYmwu_gXHemecIYY
3482:[W10-PROBE] NotificationManager.getNotificationChannelGroups argc=1 status=STUBBED caller=Lcom/fsck/k9/notification/NotificationChannelManager;.$r8$lambda$m3LNel5iYKrrYmwu_gXHemecIYY
3483:[SYNTH-EXC] f141-null-recv (deferred): Ljava/lang/NullPointerException; (Attempt to invoke interface method 'Ljava/util/List;.iterator' on a null object reference) method=Lcom/fsck/k9/notification/NotificationChannelManager;.$r8$lambda$m3LNel5iYKrrYmwu_gXHemecIYY pc=152 → uncaught (deferred frame unwind + propagate)
4239:[TRACE] 12 EXCEPTION state=nonfatal result=FAIL exc=[EXC-UNCAUGHT-TOP] [EXC-UNWIND] Ljava/lang/NullPointerException; unwound Landroidx/fragment/app/Fragment$$ExternalSyntheticLambda0;.run invoke_pc=0xf5 depth=16 [FRONTIER]

## POST (bin fea1759d58653d41, law live)
3474:[W10-PROBE] NotificationManager.createNotificationChannel argc=2 status=STUBBED caller=Lcom/fsck/k9/notification/NotificationChannelManager;.$r8$lambda$m3LNel5iYKrrYmwu_gXHemecIYY
3479:[W10-PROBE] NotificationManager.createNotificationChannel argc=2 status=STUBBED caller=Lcom/fsck/k9/notification/NotificationChannelManager;.$r8$lambda$m3LNel5iYKrrYmwu_gXHemecIYY
3482:[W10-PROBE] NotificationManager.getNotificationChannelGroups argc=1 status=STUBBED caller=Lcom/fsck/k9/notification/NotificationChannelManager;.$r8$lambda$m3LNel5iYKrrYmwu_gXHemecIYY
3483:[W10-NCGroups] NotificationManager.getNotificationChannelGroups -> empty ArrayList (AOSP never-null list law) caller=Lcom/fsck/k9/notification/NotificationChannelManager;.$r8$lambda$m3LNel5iYKrrYmwu_gXHemecIYY
