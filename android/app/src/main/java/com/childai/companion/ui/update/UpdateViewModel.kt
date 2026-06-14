package com.childai.companion.ui.update

import android.app.Application
import android.content.ActivityNotFoundException
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.provider.Settings
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
    data class InstallPermissionRequired(val apkFile: File) : UpdateState()
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
        val apkFile = when (state) {
            is UpdateState.Downloaded -> state.apkFile
            is UpdateState.InstallPermissionRequired -> state.apkFile
            else -> return
        }

        val context = getApplication<Application>()
        if (!canRequestPackageInstalls()) {
            _state.value = UpdateState.InstallPermissionRequired(apkFile)
            openInstallPermissionSettings()
            return
        }

        val apkUri: Uri = FileProvider.getUriForFile(
            context,
            "${context.packageName}.fileprovider",
            apkFile,
        )

        val intent = Intent(Intent.ACTION_VIEW).apply {
            setDataAndType(apkUri, "application/vnd.android.package-archive")
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }

        context.startActivity(intent)
    }

    fun openInstallPermissionSettings() {
        val context = getApplication<Application>()
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) {
            return
        }

        val packageUri = Uri.parse("package:${context.packageName}")
        val intent = Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES, packageUri).apply {
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        }

        try {
            context.startActivity(intent)
        } catch (_: ActivityNotFoundException) {
            val fallbackIntent = Intent(Settings.ACTION_SECURITY_SETTINGS).apply {
                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            }
            context.startActivity(fallbackIntent)
        }
    }

    private fun canRequestPackageInstalls(): Boolean {
        val context = getApplication<Application>()
        return Build.VERSION.SDK_INT < Build.VERSION_CODES.O ||
            context.packageManager.canRequestPackageInstalls()
    }

    fun dismiss() {
        dismissedVersionCode = updateInfo?.versionCode ?: dismissedVersionCode
        _state.value = UpdateState.Idle
    }
}
