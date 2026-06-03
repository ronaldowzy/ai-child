package com.childai.companion.ui.showcase

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.childai.companion.data.showcase.XiaozhantaiItem
import com.childai.companion.data.showcase.XiaozhantaiRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

class XiaozhantaiViewModel(
    private val repository: XiaozhantaiRepository = XiaozhantaiRepository(),
    private val childId: String,
) : ViewModel() {
    private val _uiState = MutableStateFlow(XiaozhantaiUiState())
    val uiState: StateFlow<XiaozhantaiUiState> = _uiState

    init {
        viewModelScope.launch {
            repository.observeItems(childId).collect { items ->
                _uiState.update {
                    it.copy(
                        items = items,
                        selectedItem = it.selectedItem?.let { selected ->
                            items.firstOrNull { item -> item.id == selected.id }
                        },
                    )
                }
            }
        }
    }

    fun selectItem(itemId: String) {
        viewModelScope.launch {
            _uiState.update {
                it.copy(selectedItem = repository.itemById(childId, itemId))
            }
        }
    }

    fun softDeleteItem(itemId: String) {
        viewModelScope.launch {
            repository.softDelete(childId, itemId)
            _uiState.update { state ->
                state.copy(selectedItem = null)
            }
        }
    }
}

data class XiaozhantaiUiState(
    val items: List<XiaozhantaiItem> = emptyList(),
    val selectedItem: XiaozhantaiItem? = null,
)
