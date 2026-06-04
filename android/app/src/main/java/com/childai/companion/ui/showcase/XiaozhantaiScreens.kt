package com.childai.companion.ui.showcase

import android.graphics.BitmapFactory
import android.net.Uri
import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.tween
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.produceState
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import com.childai.companion.R
import com.childai.companion.data.showcase.XiaozhantaiItem
import com.childai.companion.data.showcase.xiaozhantaiDisplayName
import com.childai.companion.data.showcase.xiaozhantaiNormalizeFoxQuote
import com.childai.companion.ui.theme.ChildAiCompanionTheme
import java.io.File
import java.net.URL
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

@Composable
fun XiaozhantaiListScreen(
    viewModel: XiaozhantaiViewModel,
    onBack: () -> Unit,
    onOpenItem: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    val uiState by viewModel.uiState.collectAsState()
    XiaozhantaiListContent(
        items = uiState.items,
        onBack = onBack,
        onOpenItem = onOpenItem,
        modifier = modifier,
    )
}

@Composable
fun XiaozhantaiDetailScreen(
    viewModel: XiaozhantaiViewModel,
    itemId: String?,
    onBack: () -> Unit,
    onRecallWithXiaobaohu: (XiaozhantaiItem) -> Unit,
    modifier: Modifier = Modifier,
) {
    val uiState by viewModel.uiState.collectAsState()
    val selected = uiState.selectedItem
        ?: itemId?.let { id -> uiState.items.firstOrNull { it.id == id } }
    LaunchedEffect(itemId, uiState.itemsLoaded, selected?.id) {
        if (uiState.itemsLoaded && itemId != null && selected == null) {
            onBack()
        }
    }
    XiaozhantaiDetailContent(
        item = selected,
        onBack = onBack,
        onRecallWithXiaobaohu = onRecallWithXiaobaohu,
        onDelete = { item ->
            viewModel.softDeleteItem(item.id, onDeleted = onBack)
        },
        modifier = modifier,
    )
}

@Composable
internal fun XiaozhantaiListContent(
    items: List<XiaozhantaiItem>,
    onBack: () -> Unit,
    onOpenItem: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    XiaozhantaiScaffold(
        title = "小白狐的小展台",
        onBack = onBack,
        modifier = modifier,
    ) { contentPadding ->
        if (items.isEmpty()) {
            XiaozhantaiEmptyState(
                modifier = Modifier
                    .padding(contentPadding)
                    .fillMaxSize(),
            )
        } else {
            LazyColumn(
                modifier = Modifier
                    .padding(contentPadding)
                    .fillMaxSize(),
                contentPadding = PaddingValues(horizontal = 18.dp, vertical = 18.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp),
            ) {
                items(
                    items = items.chunked(2),
                    key = { row -> row.joinToString(separator = "|") { it.id } },
                ) { row ->
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(14.dp),
                    ) {
                        row.forEach { item ->
                            XiaozhantaiThumbCard(
                                item = item,
                                onClick = { onOpenItem(item.id) },
                                modifier = Modifier.weight(1f),
                            )
                        }
                        if (row.size == 1) {
                            Spacer(modifier = Modifier.weight(1f))
                        }
                    }
                }
            }
        }
    }
}

@Composable
internal fun XiaozhantaiDetailContent(
    item: XiaozhantaiItem?,
    onBack: () -> Unit,
    onRecallWithXiaobaohu: (XiaozhantaiItem) -> Unit = {},
    onDelete: (XiaozhantaiItem) -> Unit = {},
    modifier: Modifier = Modifier,
) {
    var showDeleteConfirm by remember { androidx.compose.runtime.mutableStateOf(false) }
    XiaozhantaiScaffold(
        title = "小展台里的一件小发现",
        onBack = onBack,
        modifier = modifier,
    ) { contentPadding ->
        if (item == null) {
            XiaozhantaiEmptyState(
                modifier = Modifier
                    .padding(contentPadding)
                    .fillMaxSize(),
            )
            return@XiaozhantaiScaffold
        }
        LazyColumn(
            modifier = Modifier
                .padding(contentPadding)
                .fillMaxSize(),
            contentPadding = PaddingValues(horizontal = 22.dp, vertical = 18.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(18.dp),
        ) {
            item {
                XiaozhantaiDetailPhoto(item = item)
            }
            item {
                XiaozhantaiNamePlate(
                    name = item.name,
                    modifier = Modifier.widthIn(max = 280.dp),
                )
            }
            item {
                XiaozhantaiFoxQuote(
                    quote = item.foxQuote,
                    modifier = Modifier.fillMaxWidth(),
                )
            }
            item {
                OutlinedButton(
                    onClick = { onRecallWithXiaobaohu(item) },
                    shape = RoundedCornerShape(22.dp),
                    border = BorderStroke(1.dp, Color(0xFFB9D3E9).copy(alpha = 0.50f)),
                ) {
                    Text(
                        text = "和小白狐再聊聊它",
                        color = Color(0xFF52667B),
                    )
                }
            }
            item {
                Text(
                    text = "留下时间：${xiaozhantaiDateLabel(item.createdAt)}",
                    style = MaterialTheme.typography.labelMedium,
                    color = Color(0xFF6A7B88).copy(alpha = 0.72f),
                )
            }
            item {
                TextButton(onClick = { showDeleteConfirm = true }) {
                    Text(
                        text = "先从小展台收起来",
                        color = Color(0xFF6A7B88),
                    )
                }
            }
        }
    }
    if (item != null && showDeleteConfirm) {
        AlertDialog(
            onDismissRequest = { showDeleteConfirm = false },
            title = { Text(text = "先收起来吗？") },
            text = { Text(text = "它会从小展台里移走，照片不会出现在列表里。") },
            confirmButton = {
                Button(onClick = { onDelete(item) }) {
                    Text(text = "先收起来")
                }
            },
            dismissButton = {
                TextButton(onClick = { showDeleteConfirm = false }) {
                    Text(text = "还放着")
                }
            },
        )
    }
}

@Composable
private fun XiaozhantaiScaffold(
    title: String,
    onBack: () -> Unit,
    modifier: Modifier = Modifier,
    content: @Composable (PaddingValues) -> Unit,
) {
    Scaffold(
        modifier = modifier.fillMaxSize(),
        containerColor = Color(0xFFF8FBFF),
        topBar = {
            Surface(
                color = Color.White.copy(alpha = 0.86f),
                shadowElevation = 1.dp,
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 14.dp, vertical = 10.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    TextButton(onClick = onBack) {
                        Text(text = "返回")
                    }
                    Text(
                        text = title,
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.SemiBold,
                        color = Color(0xFF42546A),
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                        modifier = Modifier.weight(1f),
                        textAlign = TextAlign.Center,
                    )
                    Spacer(modifier = Modifier.width(64.dp))
                }
            }
        },
        content = content,
    )
}

@Composable
private fun XiaozhantaiEmptyState(
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier.padding(horizontal = 28.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center,
    ) {
        Image(
            painter = painterResource(id = R.drawable.xzt_empty_display),
            contentDescription = null,
            contentScale = ContentScale.Fit,
            modifier = Modifier
                .fillMaxWidth()
                .heightIn(max = 260.dp),
        )
        Spacer(modifier = Modifier.height(18.dp))
        Text(
            text = "这里还空空的，等你把喜欢的小发现放进来。",
            style = MaterialTheme.typography.bodyLarge,
            color = Color(0xFF52667B),
            textAlign = TextAlign.Center,
            lineHeight = MaterialTheme.typography.bodyLarge.lineHeight,
        )
    }
}

@Composable
private fun XiaozhantaiThumbCard(
    item: XiaozhantaiItem,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val density = LocalDensity.current
    val cardAlpha = remember(item.id) { Animatable(0f) }
    val cardOffsetY = remember(item.id) { Animatable(with(density) { 12.dp.toPx() }) }
    LaunchedEffect(item.id) {
        launch {
            cardAlpha.animateTo(
                targetValue = 1f,
                animationSpec = tween(durationMillis = 560),
            )
        }
        cardOffsetY.animateTo(
            targetValue = 0f,
            animationSpec = tween(durationMillis = 620),
        )
    }
    Surface(
        modifier = modifier
            .graphicsLayer {
                alpha = cardAlpha.value
                translationY = cardOffsetY.value
            }
            .clickable(onClick = onClick),
        color = Color.White.copy(alpha = 0.72f),
        shape = RoundedCornerShape(18.dp),
        shadowElevation = 1.dp,
        border = BorderStroke(1.dp, Color.White.copy(alpha = 0.72f)),
    ) {
        Column(
            modifier = Modifier.padding(horizontal = 8.dp, vertical = 10.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            XiaozhantaiThumbPhoto(
                item = item,
                modifier = Modifier
                    .fillMaxWidth()
                    .aspectRatio(1f),
            )
            Spacer(modifier = Modifier.height(8.dp))
            XiaozhantaiNamePlate(
                name = item.name,
                modifier = Modifier.fillMaxWidth(),
                compact = true,
            )
        }
    }
}

@Composable
private fun XiaozhantaiThumbPhoto(
    item: XiaozhantaiItem,
    modifier: Modifier = Modifier,
) {
    Box(modifier = modifier, contentAlignment = Alignment.Center) {
        XiaozhantaiPhotoImage(
            photoUri = item.photoUri,
            modifier = Modifier
                .fillMaxSize()
                .padding(28.dp)
                .clip(RoundedCornerShape(24.dp)),
        )
        Image(
            painter = painterResource(id = R.drawable.xzt_thumb_frame),
            contentDescription = null,
            contentScale = ContentScale.Fit,
            modifier = Modifier.fillMaxSize(),
        )
    }
}

@Composable
private fun XiaozhantaiDetailPhoto(
    item: XiaozhantaiItem,
    modifier: Modifier = Modifier,
) {
    Box(
        modifier = modifier
            .fillMaxWidth()
            .height(330.dp),
        contentAlignment = Alignment.Center,
    ) {
        XiaozhantaiPlacementEffect(
            visible = true,
            modifier = Modifier.size(310.dp),
        )
        Box(
            modifier = Modifier.size(320.dp),
            contentAlignment = Alignment.Center,
        ) {
            XiaozhantaiPhotoImage(
                photoUri = item.photoUri,
                modifier = Modifier
                    .width(238.dp)
                    .height(144.dp)
                    .clip(RoundedCornerShape(24.dp)),
            )
            Image(
                painter = painterResource(id = R.drawable.xzt_detail_frame),
                contentDescription = null,
                contentScale = ContentScale.Fit,
                modifier = Modifier.fillMaxSize(),
            )
        }
    }
}

@Composable
private fun XiaozhantaiPhotoImage(
    photoUri: String,
    modifier: Modifier = Modifier,
) {
    val bitmap by rememberXiaozhantaiPhotoBitmap(photoUri)
    if (bitmap != null) {
        Image(
            bitmap = bitmap!!,
            contentDescription = null,
            contentScale = ContentScale.Crop,
            modifier = modifier,
        )
    } else {
        Box(
            modifier = modifier.background(
                brush = Brush.linearGradient(
                    colors = listOf(
                        Color(0xFFFFF7E8),
                        Color(0xFFEAF5FF),
                    ),
                ),
            ),
            contentAlignment = Alignment.Center,
        ) {
            Text(
                text = "照片暂时看不到",
                style = MaterialTheme.typography.labelMedium,
                color = Color(0xFF7A8998).copy(alpha = 0.72f),
                textAlign = TextAlign.Center,
                modifier = Modifier.padding(horizontal = 12.dp),
            )
        }
    }
}

@Composable
private fun rememberXiaozhantaiPhotoBitmap(photoUri: String): androidx.compose.runtime.State<ImageBitmap?> {
    val context = LocalContext.current
    return produceState<ImageBitmap?>(initialValue = null, photoUri, context) {
        value = withContext(Dispatchers.IO) {
            runCatching {
                val uri = Uri.parse(photoUri)
                val bitmap = when (uri.scheme?.lowercase()) {
                    "content" -> context.contentResolver.openInputStream(uri)?.use(BitmapFactory::decodeStream)
                    "file" -> BitmapFactory.decodeFile(uri.path)
                    "http", "https" -> URL(photoUri).openStream().use(BitmapFactory::decodeStream)
                    else -> BitmapFactory.decodeFile(File(photoUri).absolutePath)
                }
                bitmap?.asImageBitmap()
            }.getOrNull()
        }
    }
}

@Composable
private fun XiaozhantaiNamePlate(
    name: String,
    modifier: Modifier = Modifier,
    compact: Boolean = false,
) {
    Box(
        modifier = modifier.height(if (compact) 42.dp else 56.dp),
        contentAlignment = Alignment.Center,
    ) {
        Image(
            painter = painterResource(id = R.drawable.xzt_name_label_plate),
            contentDescription = null,
            contentScale = ContentScale.FillBounds,
            modifier = Modifier.fillMaxSize(),
        )
        Text(
            text = xiaozhantaiDisplayName(name, if (compact) 9 else 14),
            style = if (compact) MaterialTheme.typography.labelLarge else MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.SemiBold,
            color = Color(0xFF5A4B3F),
            maxLines = 1,
            overflow = TextOverflow.Ellipsis,
            modifier = Modifier.padding(horizontal = if (compact) 16.dp else 22.dp),
        )
    }
}

@Composable
private fun XiaozhantaiFoxQuote(
    quote: String,
    modifier: Modifier = Modifier,
) {
    Surface(
        modifier = modifier,
        color = Color.White.copy(alpha = 0.76f),
        shape = RoundedCornerShape(22.dp),
        border = BorderStroke(1.dp, Color.White.copy(alpha = 0.72f)),
        shadowElevation = 1.dp,
    ) {
        Column(modifier = Modifier.padding(horizontal = 18.dp, vertical = 15.dp)) {
            Text(
                text = "小白狐当时说",
                style = MaterialTheme.typography.labelMedium,
                color = Color(0xFF7A8998),
            )
            Spacer(modifier = Modifier.height(6.dp))
            Text(
                text = xiaozhantaiNormalizeFoxQuote(quote),
                style = MaterialTheme.typography.bodyLarge,
                color = Color(0xFF465B70),
            )
        }
    }
}

@Composable
private fun XiaozhantaiPlacementEffect(
    visible: Boolean,
    modifier: Modifier = Modifier,
) {
    val alpha = remember { Animatable(0f) }
    val scale = remember { Animatable(0.92f) }
    LaunchedEffect(visible) {
        if (!visible) {
            alpha.snapTo(0f)
            scale.snapTo(0.92f)
            return@LaunchedEffect
        }
        alpha.snapTo(0f)
        scale.snapTo(0.92f)
        launch {
            scale.animateTo(
                targetValue = 1.08f,
                animationSpec = tween(durationMillis = 900),
            )
        }
        alpha.animateTo(
            targetValue = 0.75f,
            animationSpec = tween(durationMillis = 360),
        )
        alpha.animateTo(
            targetValue = 0f,
            animationSpec = tween(durationMillis = 540),
        )
    }
    Image(
        painter = painterResource(id = R.drawable.xzt_soft_light_fx),
        contentDescription = null,
        contentScale = ContentScale.Fit,
        modifier = modifier.graphicsLayer {
            this.alpha = alpha.value
            scaleX = scale.value
            scaleY = scale.value
        },
    )
}

@Preview(showBackground = true, widthDp = 390, heightDp = 780)
@Composable
private fun XiaozhantaiEmptyPreview() {
    ChildAiCompanionTheme {
        XiaozhantaiListContent(
            items = emptyList(),
            onBack = {},
            onOpenItem = {},
        )
    }
}

@Preview(showBackground = true, widthDp = 390, heightDp = 780)
@Composable
private fun XiaozhantaiListPreview() {
    ChildAiCompanionTheme {
        XiaozhantaiListContent(
            items = xiaozhantaiPreviewItems(),
            onBack = {},
            onOpenItem = {},
        )
    }
}

@Preview(showBackground = true, widthDp = 390, heightDp = 780)
@Composable
private fun XiaozhantaiDetailPreview() {
    ChildAiCompanionTheme {
        XiaozhantaiDetailContent(
            item = xiaozhantaiPreviewItems().first(),
            onBack = {},
        )
    }
}

private fun xiaozhantaiPreviewItems(): List<XiaozhantaiItem> {
    return listOf(
        XiaozhantaiItem(
            id = "stand_item_preview_001",
            photoUri = "",
            name = "小石头",
            foxQuote = "它看起来像一颗安静的小星球。",
            createdAt = 1_760_000_000_000L,
        ),
        XiaozhantaiItem(
            id = "stand_item_preview_002",
            photoUri = "",
            name = "窗边小云",
            foxQuote = "它像悄悄飘进小屋的一朵云。",
            createdAt = 1_760_000_100_000L,
        ),
    )
}

private fun xiaozhantaiDateLabel(createdAt: Long): String {
    if (createdAt <= 0L) return "刚刚"
    return SimpleDateFormat("M月d日", Locale.CHINA).format(Date(createdAt))
}
