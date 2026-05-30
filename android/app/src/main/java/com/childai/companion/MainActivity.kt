package com.childai.companion

import android.graphics.Color
import android.os.Build
import android.os.Bundle
import android.view.WindowManager
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.viewModels
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.platform.LocalContext
import androidx.core.view.WindowCompat
import com.childai.companion.data.auth.AuthRepository
import com.childai.companion.data.auth.SharedPreferencesAuthSessionStore
import com.childai.companion.ui.AppNavHost
import com.childai.companion.ui.theme.ChildAiCompanionTheme
import com.childai.companion.ui.update.UpdateDialog
import com.childai.companion.ui.update.UpdateViewModel

class MainActivity : ComponentActivity() {

    private val updateViewModel: UpdateViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Enable edge-to-edge and hide system bars for immersive experience
        WindowCompat.setDecorFitsSystemWindows(window, false)
        window.statusBarColor = Color.TRANSPARENT
        window.navigationBarColor = Color.TRANSPARENT
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
            window.attributes = window.attributes.apply {
                layoutInDisplayCutoutMode =
                    WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES
            }
        }
        val controller = WindowCompat.getInsetsController(window, window.decorView)
        controller?.hide(androidx.core.view.WindowInsetsCompat.Type.systemBars())
        controller?.systemBarsBehavior =
            androidx.core.view.WindowInsetsControllerCompat.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE

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

                // 启动时检查版本更新
                LaunchedEffect(Unit) {
                    updateViewModel.checkForUpdate()
                }

                // 显示更新弹窗
                UpdateDialog(viewModel = updateViewModel)

                AppNavHost(authRepository = authRepository)
            }
        }
    }
}
