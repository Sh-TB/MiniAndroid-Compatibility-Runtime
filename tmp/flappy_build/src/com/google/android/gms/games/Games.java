package com.google.android.gms.games;

import android.content.Intent;
import com.google.android.gms.common.api.GoogleApiClient;

/** Build-time stub: leaderboard/achievement calls are no-ops. */
public class Games {
    public static final class Leaderboards {
        public static void submitScore(GoogleApiClient c, String id, long score) {
        }

        public static Intent getLeaderboardIntent(GoogleApiClient c, String id) {
            return new Intent();
        }
    }

    public static final class Achievements {
        public static void unlock(GoogleApiClient c, String id) {
        }

        public static Intent getAchievementsIntent(GoogleApiClient c) {
            return new Intent();
        }
    }
}
