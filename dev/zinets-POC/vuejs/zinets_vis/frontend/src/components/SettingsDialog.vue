<template>
  <el-dialog
    v-model="dialogVisible"
    title="Settings"
    width="500px"
    :close-on-click-modal="false"
  >
    <el-form :model="form" label-width="150px" ref="formRef" :rules="formRules">
      <!-- API Configuration -->
      <el-divider content-position="left">
        <el-text type="primary" size="large">API Configuration</el-text>
      </el-divider>
      
      <el-form-item label="Gemini API Key" prop="geminiApiKey">
        <el-input
          v-model="form.geminiApiKey"
          type="password"
          placeholder="Enter your Google Gemini API key"
          show-password
          clearable
        />
        <div class="form-help">
          <el-text type="info" size="small">
            Required for fetching character data from Google Gemini API.
            <el-link 
              href="https://makersuite.google.com/app/apikey" 
              target="_blank" 
              type="primary"
              :underline="false"
            >
              Get API Key
            </el-link>
          </el-text>
        </div>
      </el-form-item>
      
      <!-- Test API Connection -->
      <el-form-item label="API Status">
        <div class="api-status">
          <el-tag 
            :type="apiStatus.type" 
            :effect="apiStatus.effect"
            class="status-tag"
          >
            {{ apiStatus.text }}
          </el-tag>
          <el-button 
            size="small" 
            @click="testApiConnection"
            :loading="testingApi"
            :disabled="!form.geminiApiKey"
          >
            Test Connection
          </el-button>
        </div>
      </el-form-item>
      
      <el-form-item label="Gemini Model" prop="geminiModel">
        <el-select v-model="form.geminiModel" placeholder="Select Gemini model">
          <el-option
            v-for="model in settingsStore.geminiModels"
            :key="model"
            :label="model"
            :value="model"
          />
        </el-select>
        <div class="form-help">
          <el-text type="info" size="small">
            Choose the Gemini model for character data generation
          </el-text>
        </div>
      </el-form-item>
      
      <!-- Language Preferences -->
      <el-divider content-position="left">
        <el-text type="primary" size="large">Preferences</el-text>
      </el-divider>
      
      <el-form-item label="Default Language" prop="defaultLanguage">
        <el-select v-model="form.defaultLanguage" placeholder="Select default language">
          <el-option
            v-for="lang in settingsStore.supportedLanguages"
            :key="lang.code"
            :label="lang.name"
            :value="lang.code"
          />
        </el-select>
        <div class="form-help">
          <el-text type="info" size="small">
            Language for character explanations when loading networks
          </el-text>
        </div>
      </el-form-item>
      
      <!-- Performance Settings -->
      <el-divider content-position="left">
        <el-text type="primary" size="large">Performance</el-text>
      </el-divider>
      
      <el-form-item label="Batch Size" prop="batchSize">
        <el-input-number
          v-model="form.batchSize"
          :min="1"
          :max="20"
          :step="1"
          style="width: 120px"
        />
        <div class="form-help">
          <el-text type="info" size="small">
            Number of characters to process in one API call (1-20)
          </el-text>
        </div>
      </el-form-item>
      
      <el-form-item label="Auto-cache">
        <el-switch
          v-model="form.autoCache"
          active-text="Enabled"
          inactive-text="Disabled"
        />
        <div class="form-help">
          <el-text type="info" size="small">
            Automatically use cached data before API calls
          </el-text>
        </div>
      </el-form-item>
      
      <!-- UI Settings -->
      <el-divider content-position="left">
        <el-text type="primary" size="large">User Interface</el-text>
      </el-divider>
      
      <el-form-item label="Theme" prop="theme">
        <el-select v-model="form.theme" placeholder="Select theme">
          <el-option label="Light" value="light" />
          <el-option label="Dark" value="dark" />
          <el-option label="Auto" value="auto" />
        </el-select>
        <div class="form-help">
          <el-text type="info" size="small">
            Auto theme follows your system preference
          </el-text>
        </div>
      </el-form-item>
      
      <el-form-item label="Tree Layout" prop="treeLayout">
        <el-select v-model="form.treeLayout" placeholder="Select tree layout">
          <el-option
            v-for="layout in settingsStore.treeLayoutOptions"
            :key="layout.value"
            :label="`${layout.icon} ${layout.label}`"
            :value="layout.value"
          />
        </el-select>
        <div class="form-help">
          <el-text type="info" size="small">
            Direction of tree visualization
          </el-text>
        </div>
      </el-form-item>
      
      <el-form-item label="Symbol Size">
        <el-input-number
          v-model="form.symbolSize"
          :min="20"
          :max="80"
          :step="5"
          style="width: 120px"
        />
        <div class="form-help">
          <el-text type="info" size="small">
            Size of character nodes in the tree (20-80)
          </el-text>
        </div>
      </el-form-item>
      
      <el-form-item label="Font Size">
        <el-input-number
          v-model="form.fontSize"
          :min="12"
          :max="40"
          :step="2"
          style="width: 120px"
        />
        <div class="form-help">
          <el-text type="info" size="small">
            Font size for character labels (12-40)
          </el-text>
        </div>
      </el-form-item>
      
      <el-form-item label="Animations">
        <el-switch
          v-model="form.animationEnabled"
          active-text="Enabled"
          inactive-text="Disabled"
        />
        <div class="form-help">
          <el-text type="info" size="small">
            Enable tree animations and transitions
          </el-text>
        </div>
      </el-form-item>
      
      <!-- Advanced Settings -->
      <el-divider content-position="left">
        <el-text type="primary" size="large">Advanced</el-text>
      </el-divider>
      
      <el-form-item label="Request Timeout">
        <el-input-number
          v-model="form.requestTimeout"
          :min="5"
          :max="60"
          :step="5"
          style="width: 120px"
        />
        <span style="margin-left: 8px;">seconds</span>
        <div class="form-help">
          <el-text type="info" size="small">
            Timeout for API requests (5-60 seconds)
          </el-text>
        </div>
      </el-form-item>
      
      <!-- Reset Settings -->
      <el-form-item>
        <el-button 
          type="warning" 
          plain 
          @click="resetToDefaults"
          style="width: 100%"
        >
          Reset to Defaults
        </el-button>
      </el-form-item>
    </el-form>
    
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="handleCancel" :disabled="saving">
          Cancel
        </el-button>
        <el-button @click="handleReset" :disabled="saving">
          Reset
        </el-button>
        <el-button
          type="primary"
          @click="handleSave"
          :loading="saving"
        >
          Save Settings
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script>
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

// Pinia Store
import { useSettingsStore } from '@/stores/settings'

export default {
  name: 'SettingsDialog',
  
  props: {
    visible: {
      type: Boolean,
      required: true
    }
  },
  
  emits: ['update:visible', 'settings-saved'],
  
  setup(props, { emit }) {
    // Pinia Store
    const settingsStore = useSettingsStore()
    
    // Local refs
    const formRef = ref(null)
    const saving = ref(false)
    const testingApi = ref(false)
    
    // Form data mapped from store
    const form = reactive({
      // API Settings
      geminiApiKey: '',
      geminiModel: '',
      defaultLanguage: '',
      batchSize: 10,
      autoCache: true,
      
      // UI Settings
      theme: 'light',
      treeLayout: 'TB',
      symbolSize: 40,
      fontSize: 25,
      animationEnabled: true,
      
      // Backend Settings
      requestTimeout: 30
    })
    
    const apiStatus = reactive({
      type: 'info',
      effect: 'light',
      text: 'Not tested'
    })
    
    const dialogVisible = computed({
      get: () => props.visible,
      set: (value) => emit('update:visible', value)
    })
    
    // Form validation rules
    const formRules = {
      geminiApiKey: [
        {
          validator: (rule, value, callback) => {
            if (value && !settingsStore.validateApiKey(value)) {
              callback(new Error('Invalid API key format'))
            } else {
              callback()
            }
          },
          trigger: 'blur'
        }
      ],
      geminiModel: [
        { required: true, message: 'Please select a Gemini model', trigger: 'change' }
      ],
      defaultLanguage: [
        { required: true, message: 'Please select a default language', trigger: 'change' }
      ],
      batchSize: [
        { required: true, message: 'Please set batch size', trigger: 'blur' },
        { type: 'number', min: 1, max: 20, message: 'Batch size must be between 1-20', trigger: 'blur' }
      ],
      theme: [
        { required: true, message: 'Please select a theme', trigger: 'change' }
      ],
      treeLayout: [
        { required: true, message: 'Please select a tree layout', trigger: 'change' }
      ],
      requestTimeout: [
        { required: true, message: 'Please set request timeout', trigger: 'blur' },
        { type: 'number', min: 5, max: 60, message: 'Timeout must be between 5-60 seconds', trigger: 'blur' }
      ]
    }
    
    // Methods
    function loadSettingsFromStore() {
      // Load from store to form
      Object.assign(form, {
        geminiApiKey: settingsStore.apiSettings.geminiApiKey,
        geminiModel: settingsStore.apiSettings.geminiModel,
        defaultLanguage: settingsStore.apiSettings.language,
        batchSize: settingsStore.apiSettings.chunkSize,
        autoCache: settingsStore.apiSettings.useCache,
        
        theme: settingsStore.uiSettings.theme,
        treeLayout: settingsStore.uiSettings.treeLayout,
        symbolSize: settingsStore.uiSettings.symbolSize,
        fontSize: settingsStore.uiSettings.fontSize,
        animationEnabled: settingsStore.uiSettings.animationEnabled,
        
        requestTimeout: settingsStore.backendSettings.timeout / 1000 // Convert ms to seconds
      })
    }
    
    function saveSettingsToStore() {
      try {
        // Update all store settings
        settingsStore.updateApiSettings({
          geminiApiKey: form.geminiApiKey,
          geminiModel: form.geminiModel,
          language: form.defaultLanguage,
          chunkSize: form.batchSize,
          useCache: form.autoCache
        })
        
        settingsStore.updateUiSettings({
          theme: form.theme,
          treeLayout: form.treeLayout,
          symbolSize: form.symbolSize,
          fontSize: form.fontSize,
          animationEnabled: form.animationEnabled
        })
        
        settingsStore.updateBackendSettings({
          timeout: form.requestTimeout * 1000 // Convert seconds to ms
        })
        
        return true
      } catch (error) {
        console.error('Failed to save settings:', error)
        ElMessage.error('Failed to save settings')
        return false
      }
    }
    
    async function testApiConnection() {
      if (!form.geminiApiKey) {
        ElMessage.warning('Please enter an API key first')
        return
      }
      
      // Validate API key format first
      if (!settingsStore.validateApiKey(form.geminiApiKey)) {
        apiStatus.type = 'danger'
        apiStatus.effect = 'light'
        apiStatus.text = 'Invalid API key format'
        ElMessage.error('Invalid API key format')
        return
      }
      
      testingApi.value = true
      apiStatus.type = 'info'
      apiStatus.effect = 'light'
      apiStatus.text = 'Testing...'
      
      try {
        // Test API by making a simple request
        const testUrl = `https://generativelanguage.googleapis.com/v1beta/models/${form.geminiModel}:generateContent?key=${form.geminiApiKey}`
        
        const testBody = {
          contents: [{
            parts: [{ text: 'Test' }]
          }],
          generationConfig: {
            maxOutputTokens: 10
          }
        }
        
        const response = await fetch(testUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(testBody)
        })
        
        if (response.ok) {
          apiStatus.type = 'success'
          apiStatus.effect = 'light'
          apiStatus.text = 'Connection successful'
          ElMessage.success('API connection test successful')
        } else {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }
      } catch (error) {
        apiStatus.type = 'danger'
        apiStatus.effect = 'light'
        apiStatus.text = 'Connection failed'
        ElMessage.error('API connection test failed: ' + error.message)
      } finally {
        testingApi.value = false
      }
    }
    
    function resetToDefaults() {
      ElMessageBox.confirm(
        'This will reset all settings to their default values. Continue?',
        'Reset Settings',
        {
          confirmButtonText: 'Reset',
          cancelButtonText: 'Cancel',
          type: 'warning'
        }
      ).then(() => {
        settingsStore.resetToDefaults()
        loadSettingsFromStore()
        apiStatus.type = 'info'
        apiStatus.effect = 'light'
        apiStatus.text = 'Not tested'
        ElMessage.success('Settings reset to defaults')
      }).catch(() => {
        // User cancelled
      })
    }
    
    async function handleSave() {
      try {
        // Validate form
        await formRef.value.validate()
        
        saving.value = true
        
        // Save settings to store
        if (saveSettingsToStore()) {
          // Emit saved event
          emit('settings-saved')
          
          // Close dialog
          dialogVisible.value = false
          
          ElMessage.success('Settings saved successfully')
        }
      } catch (error) {
        console.error('Form validation failed:', error)
        ElMessage.error('Please fix the form errors before saving')
      } finally {
        saving.value = false
      }
    }
    
    function handleCancel() {
      dialogVisible.value = false
      // Reload settings to discard changes
      loadSettingsFromStore()
    }
    
    function handleReset() {
      loadSettingsFromStore()
      apiStatus.type = 'info'
      apiStatus.effect = 'light'
      apiStatus.text = 'Not tested'
      ElMessage.info('Settings restored')
    }
    
    // Watch for dialog visibility to load settings
    watch(dialogVisible, (visible) => {
      if (visible) {
        loadSettingsFromStore()
      }
    })
    
    // Watch for API key changes to reset status
    watch(() => form.geminiApiKey, () => {
      apiStatus.type = 'info'
      apiStatus.effect = 'light'
      apiStatus.text = 'Not tested'
    })
    
    // Initialize settings on component mount
    loadSettingsFromStore()
    
    return {
      // Store
      settingsStore,
      
      // Refs
      formRef,
      form,
      formRules,
      saving,
      testingApi,
      apiStatus,
      
      // Computed
      dialogVisible,
      
      // Methods
      testApiConnection,
      resetToDefaults,
      handleSave,
      handleCancel,
      handleReset
    }
  }
}
</script>

<style scoped>
.form-help {
  margin-top: 8px;
}

.api-status {
  display: flex;
  align-items: center;
  gap: 10px;
}

.status-tag {
  min-width: 120px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

/* Form section spacing */
.el-divider {
  margin: 24px 0 20px 0;
}

.el-form-item {
  margin-bottom: 22px;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .dialog-footer {
    flex-direction: column;
  }
  
  .api-status {
    flex-direction: column;
    align-items: stretch;
  }
  
  .status-tag {
    text-align: center;
  }
}
</style>