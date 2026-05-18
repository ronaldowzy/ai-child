package com.childai.companion

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import com.childai.companion.ui.AppNavHost
import com.childai.companion.ui.theme.ChildAiCompanionTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        setContent {
            ChildAiCompanionTheme {
                AppNavHost()
            }
        }
    }
}
