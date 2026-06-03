package com.childai.companion.data.showcase

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import org.json.JSONObject

class XiaozhantaiModelsTest {

    @Test
    fun visibleItemsExcludeDeletedAndIncompleteItems() {
        val visible = XiaozhantaiItem(
            id = "stand_item_001",
            photoUri = "/tmp/photo.jpg",
            name = "小石头",
            foxQuote = "它看起来像一颗安静的小星球。",
            createdAt = 200L,
        )
        val deleted = visible.copy(id = "deleted", isDeleted = true)
        val noPhoto = visible.copy(id = "no_photo", photoUri = "")
        val noName = visible.copy(id = "no_name", name = "")

        val result = visibleXiaozhantaiItems(
            listOf(noPhoto, visible, deleted, noName),
        )

        assertEquals(listOf(visible), result)
        assertTrue(visible.isVisibleStandItem())
        assertFalse(deleted.isVisibleStandItem())
        assertFalse(noPhoto.isVisibleStandItem())
        assertFalse(noName.isVisibleStandItem())
    }

    @Test
    fun visibleItemsAreNewestFirst() {
        val older = XiaozhantaiItem(
            id = "older",
            photoUri = "/tmp/older.jpg",
            name = "旧发现",
            foxQuote = "旧一点也好好放着。",
            createdAt = 100L,
        )
        val newer = older.copy(
            id = "newer",
            photoUri = "/tmp/newer.jpg",
            name = "新发现",
            createdAt = 300L,
        )

        assertEquals(
            listOf(newer, older),
            visibleXiaozhantaiItems(listOf(older, newer)),
        )
    }

    @Test
    fun displayNameIsDynamicAndEllipsized() {
        assertEquals("小石头", xiaozhantaiDisplayName("  小石头  "))
        assertEquals("小发现", xiaozhantaiDisplayName(" \n\t "))
        assertEquals("很长很长…", xiaozhantaiDisplayName("很长很长的小发现名字", maxLength = 5))
    }

    @Test
    fun suggestedNameRemovesImagePrefix() {
        assertEquals("积木城堡", suggestedXiaozhantaiItemName("图片里有一个积木城堡，旁边有小灯。"))
        assertEquals("小发现", suggestedXiaozhantaiItemName(""))
    }

    @Test
    fun normalizeNameHandlesBlankLongAndWhitespace() {
        assertEquals("小发现", xiaozhantaiNormalizeName(""))
        assertEquals("小 棉花", xiaozhantaiNormalizeName("  小\n棉花  "))
        assertEquals("很长很长的小发现", xiaozhantaiNormalizeName("很长很长的小发现名字", maxLength = 8))
    }

    @Test
    fun foxQuoteUsesFirstLineOnly() {
        assertEquals(
            "我看到小石头啦",
            xiaozhantaiFoxQuoteFromReply("我看到小石头啦\n像一颗安静的小星球\n要不要给它起个名字？"),
        )
        assertEquals("小白狐看见了这个小发现。", xiaozhantaiFoxQuoteFromReply(""))
    }

    @Test
    fun itemFromJsonFallsBackNameAndFoxQuote() {
        val item = xiaozhantaiItemFromJson(
            JSONObject()
                .put("id", "stand_item_001")
                .put("photoUri", "/tmp/photo.jpg")
                .put("name", "")
                .put("foxQuote", ""),
        )

        assertEquals("小发现", item!!.name)
        assertEquals("小白狐看见了这个小发现。", item.foxQuote)
    }
}
