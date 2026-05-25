package com.childai.companion

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.runtime.remember
import androidx.compose.ui.platform.LocalContext
import com.childai.companion.data.auth.AuthRepository
import com.childai.companion.data.auth.SharedPreferencesAuthSessionStore
import com.childai.companion.ui.AppNavHost
import com.childai.companion.ui.theme.ChildAiCompanionTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        setContent {
            ChildAiCompanionTheme {
                val context = LocalContext.current
                val authRepository = remember {
                    AuthRepository(
                        sessionStore = SharedPreferencesAuthSessionStore(
                            context.applicationContext,
                        ),
                    )
                }
                AppNavHost(authRepository = authRepository)
            }
        }
    }
}
