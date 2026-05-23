package com.childai.companion.data.attachment

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.net.Uri
import java.io.ByteArrayOutputStream
import java.io.File
import kotlin.math.max

data class PhotoUploadPayload(
    val bytes: ByteArray,
    val mimeType: String = "image/jpeg",
    val fileName: String = "xiaobaohu_photo.jpg",
)

object PhotoUploadPreparer {
    private const val MAX_DIMENSION = 1280
    private const val DEFAULT_JPEG_QUALITY = 82
    private const val MAX_IMAGE_BYTES = 4_800_000
    private const val MAX_SOURCE_BYTES = 16_000_000

    fun prepareJpegUpload(
        photoFile: File,
        fileName: String = photoFile.name.ifBlank { "xiaobaohu_photo.jpg" },
    ): PhotoUploadPayload {
        val bitmap = decodeScaledBitmap(photoFile.readBytes(), MAX_DIMENSION)
            ?: error("photo decode failed")
        val jpegBytes = compressJpegWithinLimit(bitmap)
        return PhotoUploadPayload(
            bytes = jpegBytes,
            mimeType = "image/jpeg",
            fileName = fileName,
        )
    }

    fun prepareJpegUpload(
        context: Context,
        uri: Uri,
        fileName: String = "xiaobaohu_gallery.jpg",
    ): PhotoUploadPayload {
        val sourceBytes = context.contentResolver.openInputStream(uri)?.use { input ->
            input.readBytes()
        } ?: error("image open failed")
        if (sourceBytes.size > MAX_SOURCE_BYTES) {
            error("selected image is too large")
        }
        val bitmap = decodeScaledBitmap(sourceBytes, MAX_DIMENSION)
            ?: error("image decode failed")
        val jpegBytes = compressJpegWithinLimit(bitmap)
        return PhotoUploadPayload(
            bytes = jpegBytes,
            mimeType = "image/jpeg",
            fileName = fileName,
        )
    }

    private fun decodeScaledBitmap(
        bytes: ByteArray,
        maxDimension: Int,
    ): Bitmap? {
        val bounds = BitmapFactory.Options().apply {
            inJustDecodeBounds = true
        }
        BitmapFactory.decodeByteArray(bytes, 0, bytes.size, bounds)
        val largestSide = max(bounds.outWidth, bounds.outHeight)
        val sampleSize = generateSequence(1) { it * 2 }
            .first { sample -> largestSide / sample <= maxDimension || sample >= 16 }

        return BitmapFactory.decodeByteArray(
            bytes,
            0,
            bytes.size,
            BitmapFactory.Options().apply {
                inSampleSize = sampleSize
            },
        )?.let { bitmap ->
            if (max(bitmap.width, bitmap.height) <= maxDimension) {
                bitmap
            } else {
                val scale = maxDimension.toFloat() / max(bitmap.width, bitmap.height).toFloat()
                Bitmap.createScaledBitmap(
                    bitmap,
                    (bitmap.width * scale).toInt().coerceAtLeast(1),
                    (bitmap.height * scale).toInt().coerceAtLeast(1),
                    true,
                ).also {
                    if (it !== bitmap) bitmap.recycle()
                }
            }
        }
    }

    private fun compressJpegWithinLimit(bitmap: Bitmap): ByteArray {
        var quality = DEFAULT_JPEG_QUALITY
        var bytes: ByteArray
        do {
            bytes = ByteArrayOutputStream().use { output ->
                bitmap.compress(Bitmap.CompressFormat.JPEG, quality, output)
                output.toByteArray()
            }
            quality -= 10
        } while (bytes.size > MAX_IMAGE_BYTES && quality >= 52)
        if (bytes.size > MAX_IMAGE_BYTES) {
            error("photo is too large after compression")
        }
        return bytes
    }
}
