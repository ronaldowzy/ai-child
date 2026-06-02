import java.util.Properties

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
}

val appVersionProperties = Properties().apply {
    val repoRoot = rootProject.layout.projectDirectory.asFile.parentFile
    val versionFile = repoRoot.resolve("release/app_version.properties")
    if (versionFile.isFile) {
        versionFile.inputStream().use(::load)
    }
}

val conversationApiBaseUrl: String =
    providers.gradleProperty("conversationApiBaseUrl").orNull ?: "http://192.168.0.101:8000/"
val releaseStoreFilePath: String? =
    providers.gradleProperty("releaseStoreFile").orNull ?: System.getenv("CHILD_AI_RELEASE_STORE_FILE")
val releaseStorePassword: String? =
    providers.gradleProperty("releaseStorePassword").orNull ?: System.getenv("CHILD_AI_RELEASE_STORE_PASSWORD")
val releaseKeyAlias: String? =
    providers.gradleProperty("releaseKeyAlias").orNull ?: System.getenv("CHILD_AI_RELEASE_KEY_ALIAS")
val releaseKeyPassword: String? =
    providers.gradleProperty("releaseKeyPassword").orNull ?: System.getenv("CHILD_AI_RELEASE_KEY_PASSWORD")
val hasReleaseSigning: Boolean = listOf(
    releaseStoreFilePath,
    releaseStorePassword,
    releaseKeyAlias,
    releaseKeyPassword,
).all { !it.isNullOrBlank() }

android {
    namespace = "com.childai.companion"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.childai.companion"
        minSdk = 26
        targetSdk = 35
        versionCode = appVersionProperties.getProperty("versionCode")?.toIntOrNull() ?: 2
        versionName = appVersionProperties.getProperty("versionName") ?: "0.2.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        buildConfigField(
            "String",
            "CONVERSATION_API_BASE_URL",
            "\"$conversationApiBaseUrl\"",
        )
    }

    signingConfigs {
        if (hasReleaseSigning) {
            create("release") {
                storeFile = file(releaseStoreFilePath!!)
                storePassword = releaseStorePassword
                keyAlias = releaseKeyAlias
                keyPassword = releaseKeyPassword
            }
        }
    }

    buildTypes {
        getByName("release") {
            isMinifyEnabled = false
            if (hasReleaseSigning) {
                signingConfig = signingConfigs.getByName("release")
            }
        }
    }

    buildFeatures {
        compose = true
        buildConfig = true
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }

    testOptions {
        unitTests.isReturnDefaultValues = true
    }
}

dependencies {
    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.8.7")
    implementation("androidx.lifecycle:lifecycle-viewmodel-ktx:2.8.7")
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.8.7")
    implementation("androidx.activity:activity-compose:1.9.3")

    implementation(platform("androidx.compose:compose-bom:2024.10.00"))
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-graphics")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.compose.material3:material3")

    testImplementation("junit:junit:4.13.2")
    testImplementation("org.json:json:20240303")
    testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:1.8.1")

    debugImplementation("androidx.compose.ui:ui-tooling")
    debugImplementation("androidx.compose.ui:ui-test-manifest")
}
