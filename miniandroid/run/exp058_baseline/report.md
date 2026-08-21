# EXP-058 Baseline Report

## Build
- Commit: 0d8ae7c
- Exit code: 0

## Core Metrics
- Unique methods: 501
- HALT events: 0
- EXCEPTION events: 10
- CLASS_INIT events: 56
- Instructions: 66010
- Duration: Duration: 15396.72ms
- Peak RSS: [MEM] execute_on_create: post-execute_apk_with_activity RSS=501.191 MB

## Login Path Progress
- getIntent: 2 calls
- isClientActivated: 12 mentions
- getFragmentStack: 6 mentions
- getClientNotActivated: 4 mentions
- LoginActivity: 3 mentions
- addFragmentToStack: 4 mentions
- Fragment.onCreate: 4 mentions
- onCreateView: 0 mentions

## Fragment-related methods reached


## Last 10 unique methods
[METHOD-IN] Lorg/telegram/ui/RestrictedLanguagesSelectActivity;.getExtendedDoNotTranslate (bytecode_size=47)
[METHOD-IN] Lorg/telegram/ui/Stories/LiveStoryPipOverlay;.<clinit> (bytecode_size=48)
[METHOD-IN] Lorg/telegram/ui/Stories/LiveStoryPipOverlay;.dismiss (bytecode_size=7)
[METHOD-IN] Lorg/telegram/ui/Stories/LiveStoryPipOverlay;.isVisible (bytecode_size=5)
[METHOD-IN] Lorg/telegram/ui/Stories/PeerStoriesView;.updatePosition (bytecode_size=4259)
[METHOD-IN] Lorg/telegram/ui/Stories/StoriesIntro;.startAnimation (bytecode_size=104)
[METHOD-IN] Lorg/telegram/ui/Stories/StoryViewer;.getCurrentPeerView (bytecode_size=11)
[METHOD-IN] Lorg/telegram/ui/Stories/StoryViewer;.onResume (bytecode_size=43)
[METHOD-IN] Lorg/telegram/ui/Stories/StoryViewer;.updatePipSource (bytecode_size=1)
[METHOD-IN] Lorg/telegram/ui/Stories/StoryViewer;.updatePlayingMode (bytecode_size=104)

## Shadow report
{
  "activity_lifecycle_state": 0,
  "calls_dispatched": 6508,
  "calls_fallback": 6208,
  "calls_handled": 300,
  "content_view_id": 0,
  "coverage_percent": 4.609711124769515,
  "current_activity_class": "",
  "current_activity_id": 0,
  "handler_queue_depth": 0,
  "intent_pending": false,
  "shadow_count": 8,
  "shadows": [
    {
      "implemented_methods": [
        "currentThread",
        "getName",
        "getId",
        "getStackTrace",
        "isAlive",
