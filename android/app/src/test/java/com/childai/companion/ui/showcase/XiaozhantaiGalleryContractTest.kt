package com.childai.companion.ui.showcase

import com.childai.companion.data.showcase.XiaozhantaiItem
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Test

class XiaozhantaiGalleryContractTest {
    @Test
    fun childFacingCopyUsesApprovedS2Text() {
        assertEquals("小展台", XiaozhantaiGalleryCopy.entrance)
        assertEquals("我的小展台", XiaozhantaiGalleryCopy.title)
        assertEquals("这里还空空的", XiaozhantaiGalleryCopy.emptyLineOne)
        assertEquals("等你和小白狐放进一个小发现", XiaozhantaiGalleryCopy.emptyLineTwo)
        assertEquals("小白狐那时说", XiaozhantaiGalleryCopy.foxQuoteLabel)
        assertEquals("关上", XiaozhantaiGalleryCopy.close)
    }

    @Test
    fun listCardModelContainsThumbnailNameAndSavedTime() {
        val item = XiaozhantaiItem(
            id = "stand_item_1",
            photoUri = "/tmp/synthetic-xiaozhantai-photo.jpg",
            name = "蓝盖盖转轮",
            foxQuote = "门上的圆锁轻轻转了一小下",
            createdAt = 1_762_473_600_000L,
        )

        val model = item.toGalleryCardUiModel()

        assertEquals("stand_item_1", model.id)
        assertEquals("/tmp/synthetic-xiaozhantai-photo.jpg", model.photoUri)
        assertEquals("蓝盖盖转轮", model.name)
        assertEquals("11月7日", model.savedAtLabel)
    }

    @Test
    fun detailModelContainsLargePhotoNameAndFoxQuote() {
        val item = XiaozhantaiItem(
            id = "stand_item_2",
            photoUri = "/tmp/synthetic-xiaozhantai-detail.jpg",
            name = "小月亮盾牌",
            foxQuote = "小门被它逗得晃了一下",
            createdAt = 0L,
        )

        val model = item.toGalleryDetailUiModel()

        assertEquals("/tmp/synthetic-xiaozhantai-detail.jpg", model.photoUri)
        assertEquals("小月亮盾牌", model.name)
        assertEquals("小门被它逗得晃了一下", model.foxQuote)
        assertEquals("刚刚", item.toGalleryCardUiModel().savedAtLabel)
    }

    @Test
    fun s2GalleryCopyDoesNotIntroduceForbiddenSystems() {
        val forbidden = listOf(
            "删除",
            "收起来",
            "搜索",
            "分类",
            "百宝箱",
            "图鉴",
            "背包",
            "奖励",
            "积分",
            "等级",
            "任务",
            "打卡",
            "收藏",
            "通关",
        )

        XiaozhantaiGalleryCopy.approvedChildFacingCopy().forEach { copy ->
            forbidden.forEach { marker ->
                assertFalse("$copy should not contain $marker", copy.contains(marker))
            }
        }
    }
}
