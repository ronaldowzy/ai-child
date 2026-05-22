package com.childai.companion.ui.chat

import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.platform.LocalContext
import androidx.core.content.FileProvider
import com.childai.companion.data.attachment.PhotoDataUriEncoder
import java.io.File

@Composable
internal fun rememberImageInputLaunchers(
    onCaptured: (imageDataUri: String, imagePurpose: String) -> Unit,
    onFailed: (String) -> Unit,
): ImageInputLaunchers {
    val context = LocalContext.current
    var pendingPhotoFile by rememberSaveable { mutableStateOf<String?>(null) }
    var pendingImagePurpose by rememberSaveable { mutableStateOf(IMAGE_PURPOSE_SHARE) }
    val photoLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.TakePicture(),
    ) { success ->
        val photoFile = pendingPhotoFile?.let(::File)
        val imagePurpose = pendingImagePurpose
        pendingPhotoFile = null
        pendingImagePurpose = IMAGE_PURPOSE_SHARE
        if (!success || photoFile == null) {
            photoFile?.delete()
            onFailed("这张照片没有拍好，我们再拍一次。")
            return@rememberLauncherForActivityResult
        }
        runCatching {
            PhotoDataUriEncoder.encodeJpegDataUri(photoFile)
        }.onSuccess { imageDataUri ->
            onCaptured(imageDataUri, imagePurpose)
        }.onFailure {
            onFailed("这张照片没有处理好，我们再拍一次。")
        }
        photoFile.delete()
    }
    val galleryLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.GetContent(),
    ) { uri ->
        val imagePurpose = pendingImagePurpose
        pendingImagePurpose = IMAGE_PURPOSE_SHARE
        if (uri == null) {
            onFailed("这张图片没有选好，我们再试一次。")
            return@rememberLauncherForActivityResult
        }
        runCatching {
            PhotoDataUriEncoder.encodeJpegDataUri(context, uri)
        }.onSuccess { imageDataUri ->
            onCaptured(imageDataUri, imagePurpose)
        }.onFailure {
            onFailed("这张图片没有处理好，我们再选一次。")
        }
    }

    return ImageInputLaunchers(
        capturePhoto = { imagePurpose ->
            runCatching {
                val photoDirectory = File(context.cacheDir, "photo_capture").apply {
                    mkdirs()
                }
                val photoFile = File.createTempFile("xiaobaohu_photo_", ".jpg", photoDirectory)
                val photoUri = FileProvider.getUriForFile(
                    context,
                    "${context.packageName}.fileprovider",
                    photoFile,
                )
                pendingPhotoFile = photoFile.absolutePath
                pendingImagePurpose = imagePurpose
                photoLauncher.launch(photoUri)
            }.onFailure {
                pendingPhotoFile?.let(::File)?.delete()
                pendingPhotoFile = null
                pendingImagePurpose = IMAGE_PURPOSE_SHARE
                onFailed("现在没有打开相机，我们请大人检查一下。")
            }
        },
        pickFromGallery = { imagePurpose ->
            pendingImagePurpose = imagePurpose
            galleryLauncher.launch("image/*")
        },
    )
}

internal data class ImageInputLaunchers(
    val capturePhoto: (String) -> Unit,
    val pickFromGallery: (String) -> Unit,
)
