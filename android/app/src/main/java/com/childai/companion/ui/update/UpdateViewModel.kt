package com.childai.companion.ui.update

import android.app.Application
import android.content.Intent
import android.net.Uri
import androidx.core.content.FileProvider
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.childai.companion.BuildConfig
import com.childai.companion.config.DevSettings
import com.childai.companion.data.version.VersionCheckResult
import com.childai.companion.data.version.VersionRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.io.File

sealed class UpdateState {
    data object Idle : UpdateState()
    data object Checking : UpdateState()
    data class Available(val info: VersionCheckResult) : UpdateState()
    data class Downloading(val progress: Float) : UpdateState()
    data class Downloaded(val apkFile: File) : UpdateState()
    data class Error(val message: String) : UpdateState()
    data object NoUpdate : UpdateState()
}

class UpdateViewModel(application: Application) : AndroidViewModel(application) {

    private val repository = VersionRepository(application, DevSettings.conversationApiBaseUrl)

    private val _state = MutableStateFlow<UpdateState>(UpdateState.Idle)
    val state: StateFlow<UpdateState> = _state.asStateFlow()

    private var updateInfo: VersionCheckResult? = null
    private var dismissedVersionCode: Int? = null

    fun checkForUpdate() {
        if (
            _state.value is UpdateState.Checking ||
            _state.value is UpdateState.Downloading ||
            _state.value is UpdateState.Available ||
            _state.value is UpdateState.Downloaded
        ) {
            return
        }

        viewModelScope.launch {
            _state.value = UpdateState.Checking

            try {
                val currentVersionCode = BuildConfig.VERSION_CODE
                val result = repository.checkForUpdate(currentVersionCode)

                if (result != null) {
                    if (dismissedVersionCode == result.versionCode) {
                        _state.value = UpdateState.Idle
                        return@launch
                    }
                    updateInfo = result
                    _state.value = UpdateState.Available(result)
                } else {
                    _state.value = UpdateState.NoUpdate
                }
            } catch (e: Exception) {
                _state.value = UpdateState.Error(e.message ?: "检查更新失败")
            }
        }
    }

    fun startDownload() {
        val info = updateInfo ?: return

        viewModelScope.launch {
            _state.value = UpdateState.Downloading(0f)

            try {
                val apkFile = repository.downloadApk(info.downloadUrl) { progress ->
                    _state.value = UpdateState.Downloading(progress)
                }
                _state.value = UpdateState.Downloaded(apkFile)
            } catch (e: Exception) {
                _state.value = UpdateState.Error(e.message ?: "下载失败")
            }
        }
    }

    fun installApk() {
        val state = _state.value
        if (state !is UpdateState.Downloaded) return

        val context = getApplication<Application>()
        val apkUri: Uri = FileProvider.getUriForFile(
            context,
            "${context.packageName}.fileprovider",
            state.apkFile,
        )

        val intent = Intent(Intent.ACTION_VIEW).apply {
            setDataAndType(apkUri, "application/vnd.android.package-archive")
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }

        context.startActivity(intent)
    }

    fun dismiss() {
        dismissedVersionCode = updateInfo?.versionCode ?: dismissedVersionCode
        _state.value = UpdateState.Idle
    }
}
