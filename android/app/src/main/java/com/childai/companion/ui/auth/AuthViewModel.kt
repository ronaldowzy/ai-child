package com.childai.companion.ui.auth

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.childai.companion.data.auth.AuthLoginRequest
import com.childai.companion.data.auth.AuthRegisterRequest
import com.childai.companion.data.auth.AuthRepository
import com.childai.companion.data.auth.SavedAuthSession
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

class AuthViewModel(
    private val repository: AuthRepository,
    private val dispatcher: CoroutineDispatcher = Dispatchers.Main.immediate,
) : ViewModel() {
    private val _uiState = MutableStateFlow(
        AuthUiState(session = repository.savedSession()),
    )
    val uiState: StateFlow<AuthUiState> = _uiState

    init {
        if (_uiState.value.isLoggedIn) {
            refreshSavedSession()
        }
    }

    fun updateMode(mode: AuthMode) {
        _uiState.update { it.copy(mode = mode, errorMessage = null) }
    }

    fun updateUsername(value: String) {
        _uiState.update { it.copy(username = value, errorMessage = null) }
    }

    fun updatePassword(value: String) {
        _uiState.update { it.copy(password = value, errorMessage = null) }
    }

    fun updateChildNickname(value: String) {
        _uiState.update { it.copy(childNickname = value, errorMessage = null) }
    }

    fun updateChildAge(value: String) {
        _uiState.update { it.copy(childAge = value, errorMessage = null) }
    }

    fun updateChildInterests(value: String) {
        _uiState.update { it.copy(childInterestsText = value, errorMessage = null) }
    }

    fun submit() {
        val state = _uiState.value
        if (state.isSubmitting) return
        if (state.username.trim().length < 3 || state.password.length < 8) {
            _uiState.update {
                it.copy(errorMessage = "账号至少 3 个字符，密码至少 8 个字符。")
            }
            return
        }
        _uiState.update { it.copy(isSubmitting = true, errorMessage = null) }
        viewModelScope.launch(dispatcher) {
            runCatching {
                if (state.mode == AuthMode.Register) {
                    repository.register(
                        AuthRegisterRequest(
                            username = state.username.trim(),
                            password = state.password,
                            childNickname = state.childNickname.trim(),
                            childAge = state.childAge.trim().toIntOrNull(),
                            childInterests = state.childInterestList(),
                        ),
                    )
                } else {
                    repository.login(
                        AuthLoginRequest(
                            username = state.username.trim(),
                            password = state.password,
                        ),
                    )
                }
            }.onSuccess { session ->
                _uiState.update {
                    it.copy(
                        session = session,
                        isSubmitting = false,
                        password = "",
                        errorMessage = null,
                    )
                }
            }.onFailure {
                _uiState.update {
                    it.copy(
                        isSubmitting = false,
                        errorMessage = if (state.mode == AuthMode.Register) {
                            "创建或登录没有成功，请家长检查账号信息和后端服务。"
                        } else {
                            "登录没有成功，请家长检查账号和密码。"
                        },
                    )
                }
            }
        }
    }

    fun logout() {
        _uiState.update { it.copy(isSubmitting = true, errorMessage = null) }
        viewModelScope.launch(dispatcher) {
            repository.logout()
            _uiState.update {
                AuthUiState(mode = AuthMode.Login)
            }
        }
    }

    private fun refreshSavedSession() {
        viewModelScope.launch(dispatcher) {
            runCatching {
                repository.refreshAccount()
            }.onSuccess { session ->
                _uiState.update { it.copy(session = session) }
            }.onFailure {
                repository.logout()
                _uiState.update { AuthUiState(mode = AuthMode.Login) }
            }
        }
    }
}

enum class AuthMode {
    Login,
    Register,
}

data class AuthUiState(
    val session: SavedAuthSession = SavedAuthSession.Empty,
    val mode: AuthMode = AuthMode.Login,
    val username: String = "",
    val password: String = "",
    val childNickname: String = "",
    val childAge: String = "",
    val childInterestsText: String = "",
    val isSubmitting: Boolean = false,
    val errorMessage: String? = null,
) {
    val isLoggedIn: Boolean
        get() = session.isPresent

    fun childInterestList(): List<String> {
        return childInterestsText
            .lines()
            .flatMap { it.split("，", "、", ",") }
            .map { it.trim() }
            .filter { it.isNotEmpty() }
    }
}
