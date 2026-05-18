package com.childai.companion.ui.chat

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.sizeIn
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.unit.dp

@Composable
fun CartoonAgentView(modifier: Modifier = Modifier) {
    Box(
        modifier = modifier
            .fillMaxWidth(0.72f)
            .sizeIn(minWidth = 180.dp, maxWidth = 320.dp)
            .aspectRatio(1f),
    ) {
        Canvas(modifier = Modifier.matchParentSize()) {
            drawFoxAgent()
        }
    }
}

private fun DrawScope.drawFoxAgent() {
    val center = Offset(size.width / 2f, size.height / 2f)
    val foxOrange = Color(0xFFD88945)
    val foxCream = Color(0xFFFFF1DD)
    val foxBrown = Color(0xFF604230)
    val leafGreen = Color(0xFF5B7C5A)
    val softShadow = Color(0x263E4D39)

    drawOval(
        color = softShadow,
        topLeft = Offset(size.width * 0.18f, size.height * 0.78f),
        size = Size(size.width * 0.64f, size.height * 0.10f),
    )

    drawCircle(
        color = foxOrange,
        radius = size.minDimension * 0.31f,
        center = Offset(center.x, size.height * 0.47f),
    )

    drawEar(
        outerColor = foxOrange,
        innerColor = foxCream,
        points = listOf(
            Offset(size.width * 0.25f, size.height * 0.36f),
            Offset(size.width * 0.33f, size.height * 0.12f),
            Offset(size.width * 0.47f, size.height * 0.33f),
        ),
    )
    drawEar(
        outerColor = foxOrange,
        innerColor = foxCream,
        points = listOf(
            Offset(size.width * 0.75f, size.height * 0.36f),
            Offset(size.width * 0.67f, size.height * 0.12f),
            Offset(size.width * 0.53f, size.height * 0.33f),
        ),
    )

    drawOval(
        color = foxCream,
        topLeft = Offset(size.width * 0.31f, size.height * 0.45f),
        size = Size(size.width * 0.38f, size.height * 0.28f),
    )

    drawCircle(
        color = foxBrown,
        radius = size.minDimension * 0.026f,
        center = Offset(size.width * 0.41f, size.height * 0.44f),
    )
    drawCircle(
        color = foxBrown,
        radius = size.minDimension * 0.026f,
        center = Offset(size.width * 0.59f, size.height * 0.44f),
    )

    drawCircle(
        color = foxBrown,
        radius = size.minDimension * 0.022f,
        center = Offset(size.width * 0.50f, size.height * 0.53f),
    )
    drawArc(
        color = foxBrown,
        startAngle = 24f,
        sweepAngle = 132f,
        useCenter = false,
        topLeft = Offset(size.width * 0.43f, size.height * 0.53f),
        size = Size(size.width * 0.14f, size.height * 0.10f),
        style = Stroke(width = size.minDimension * 0.012f),
    )

    drawRoundRect(
        color = leafGreen,
        topLeft = Offset(size.width * 0.37f, size.height * 0.68f),
        size = Size(size.width * 0.26f, size.height * 0.10f),
        cornerRadius = androidx.compose.ui.geometry.CornerRadius(
            x = size.minDimension * 0.04f,
            y = size.minDimension * 0.04f,
        ),
    )
}

private fun DrawScope.drawEar(
    outerColor: Color,
    innerColor: Color,
    points: List<Offset>,
) {
    val outerPath = Path().apply {
        moveTo(points[0].x, points[0].y)
        lineTo(points[1].x, points[1].y)
        lineTo(points[2].x, points[2].y)
        close()
    }
    drawPath(path = outerPath, color = outerColor)

    val innerPath = Path().apply {
        moveTo((points[0].x + points[1].x) / 2f, (points[0].y + points[1].y) / 2f)
        lineTo(points[1].x, points[1].y + size.height * 0.05f)
        lineTo((points[1].x + points[2].x) / 2f, (points[1].y + points[2].y) / 2f)
        close()
    }
    drawPath(path = innerPath, color = innerColor)
}
