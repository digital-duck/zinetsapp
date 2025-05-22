<template>
  <el-dialog
    v-model="dialogVisible"
    title="Load Character Network"
    width="600px"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
  >
    <el-form :model="form" label-width="120px" ref="formRef" :rules="formRules">
      <!-- Input Method Selection -->
      <el-form-item label="Input Method">
        <el-radio-group v-model="form.inputMethod">
          <el-radio label="text">Paste Markdown Text</el-radio>
          <el-radio label="file">Upload File</el-radio>
          <el-radio label="preset">Use Preset Network</el-radio>
        </el-radio-group>
      </el-form-item>
      
      <!-- Text Input -->
      <el-form-item
        v-if="form.inputMethod === 'text'"
        label="Markdown Text"
        prop="markdownText"
      >
        <el-input
          v-model="form.markdownText"
          type="textarea"
          :rows="12"
          placeholder="Enter your character network in markdown format..."
          show-word-limit
        />
        <div class="input-help">
          <el-text type="info" size="small">
            Format: Character names with indentation. Use parentheses for decomposition.
          </el-text>
        </div>
      </el-form-item>
      
      <!-- File Upload -->
      <el-form-item
        v-if="form.inputMethod === 'file'"
        label="Upload File"
        prop="file"
      >
        <el-upload
          ref="uploadRef"
          :auto-upload="false"
          :on-change="handleFileChange"
          :on-remove="handleFileRemove"
          :show-file-list="true"
          :limit="1"
          accept=".md,.txt"
          drag
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">
            Drop file here or <em>click to upload</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              Only .md and .txt files are supported
            </div>
          </template>
        </el-upload>
        <div v-if="form.fileContent" class="file-preview">
          <el-text type="success" size="small">
            File loaded successfully ({{ form.fileContent.split('\n').length }} lines)
          </el-text>
        </div>
      </el-form-item>
      
      <!-- Preset Selection -->
      <el-form-item
        v-if="form.inputMethod === 'preset'"
        label="Preset Network"
        prop="preset"
      >
        <el-select v-model="form.preset" placeholder="Choose a preset network">
          <el-option
            v-for="preset in presetOptions"
            :key="preset.value"
            :label="preset.label"
            :value="preset.value"
          >
            <span>{{ preset.label }}</span>
            <span style="color: #8492a6; font-size: 13px; margin-left: 10px;">
              {{ preset.description }}
            </span>
          </el-option>
        </el-select>
        <div v-if="form.preset" class="preset-preview">
          <el-text type="info" size="small">
            Preview: {{ getPresetPreview(form.preset) }}
          </el-text>
        </div>
      </el-form-item>
      
      <!-- Language Selection -->
      <el-form-item label="Language" prop="language">
        <el-select v-model="form.language" placeholder="Select language">
          <el-option
            v-for="lang in settingsStore.supportedLanguages"
            :key="lang.code"
            :label="lang.name"
            :value="lang.code"
          />
        </el-select>
      </el-form-item>
      
      <!-- Options -->
      <el-form-item label="Options">
        <div class="option-group">
          <el-checkbox v-model="form.useCache">
            <span>Use cached data</span>
            <el-tooltip content="Check cache before calling LLM API to save tokens">
              <el-icon style="margin-left: 5px;"><question-filled /></el-icon>
            </el-tooltip>
          </el-checkbox>
          
          <el-checkbox v-model="form.useLLM">
            <span>Fetch from LLM API</span>
            <el-tooltip content="Call Gemini API for missing character data">
              <el-icon style="margin-left: 5px;"><question-filled /></el-icon>
            </el-tooltip>
          </el-checkbox>
        </div>
        
        <div v-if="!form.useLLM" class="warning-text">
          <el-text type="warning" size="small">
            Only cached data and placeholders will be used
          </el-text>
        </div>
        
        <div v-if="form.useLLM && !settingsStore.hasGeminiApiKey" class="warning-text">
          <el-text type="danger" size="small">
            Gemini API key not configured. Please set it in Settings.
          </el-text>
        </div>
      </el-form-item>
      
      <!-- Validation Summary -->
      <el-form-item v-if="validationResult" label="Validation">
        <div class="validation-summary">
          <el-alert
            :type="validationResult.valid ? 'success' : 'error'"
            :title="validationResult.valid ? 'Markdown format is valid' : 'Markdown format has errors'"
            :description="getValidationDescription()"
            show-icon
            :closable="false"
          />
        </div>
      </el-form-item>
    </el-form>
    
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="handleCancel" :disabled="networkStore.loading">
          Cancel
        </el-button>
        <el-button @click="validateMarkdown" :disabled="!canValidate">
          Validate
        </el-button>
        <el-button
          type="primary"
          @click="handleSubmit"
          :loading="networkStore.loading"
          :disabled="!canSubmit"
        >
          Load Network
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script>
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled, QuestionFilled } from '@element-plus/icons-vue'

// Pinia Stores
import { useNetworkStore } from '@/stores/network'
import { useSettingsStore } from '@/stores/settings'

// Preset networks
const PRESET_NETWORKS = {
  heart: {
    label: 'Heart (心) - Mind & Emotions',
    description: 'Characters related to mind and emotions',
    content: `心
- 想(相+心)
    - 愿(原+心)
    - 惟(忄+隹)
- 情(忄+青)
    - 愛(爫+冖+心+夊)
    - 恋(亦+心)
- 忘(亡+心)
    - 怯(忄+去)
    - 悔(忄+每)
- 志(士+心)
    - 意(立+心)
    - 思(田+心)`
  },
  
  water: {
    label: 'Water (水) - Water Elements',
    description: 'Characters related to water',
    content: `水
- 氵
- 冰(氵+丶)
- 江(氵+工)
- 河(氵+可)
    - 湖(氵+胡)
    - 海(氵+每)
- 泉(白+水)
- 雨(☂)
    - 雪(雨+彗)
    - 雷(雨+田)`
  },
  
  algae: {
    label: 'Algae (藻) - Plant Network',
    description: 'Original algae-based network',
    content: `藻
- 艹
- 澡(氵+喿)
    - 氵
    - 喿(品+木)
        - 品(口+口+口)
                - 口 
                - 口 
                - 口 
        - 木`
  }
}

export default {
  name: 'NetworkInput',
  components: {
    UploadFilled,
    QuestionFilled
  },
  
  props: {
    visible: {
      type: Boolean,
      required: true
    }
  },
  
  emits: ['update:visible', 'network-loaded'],
  
  setup(props, { emit }) {
    // Pinia Stores
    const networkStore = useNetworkStore()
    const settingsStore = useSettingsStore()
    
    // Local refs
    const formRef = ref(null)
    const uploadRef = ref(null)
    const validationResult = ref(null)
    
    const form = reactive({
      inputMethod: 'preset',
      markdownText: '',
      file: null,
      fileContent: '',
      preset: 'heart',
      language: settingsStore.apiSettings.language,
      useCache: settingsStore.apiSettings.useCache,
      useLLM: true
    })
    
    const dialogVisible = computed({
      get: () => props.visible,
      set: (value) => emit('update:visible', value)
    })
    
    const presetOptions = computed(() => {
      return Object.entries(PRESET_NETWORKS).map(([key, preset]) => ({
        value: key,
        label: preset.label,
        description: preset.description
      }))
    })
    
    const canValidate = computed(() => {
      return getMarkdownContent() !== ''
    })
    
    const canSubmit = computed(() => {
      if (!validationResult.value) return false
      return validationResult.value.valid && getMarkdownContent() !== ''
    })
    
    // Form validation rules
    const formRules = {
      markdownText: [
        { required: true, message: 'Please enter markdown text', trigger: 'blur' }
      ],
      file: [
        { required: true, message: 'Please select a file', trigger: 'change' }
      ],
      preset: [
        { required: true, message: 'Please select a preset', trigger: 'change' }
      ],
      language: [
        { required: true, message: 'Please select a language', trigger: 'change' }
      ]
    }
    
    // Methods
    function getMarkdownContent() {
      switch (form.inputMethod) {
        case 'text':
          return form.markdownText
        case 'file':
          return form.fileContent
        case 'preset':
          return form.preset ? PRESET_NETWORKS[form.preset].content : ''
        default:
          return ''
      }
    }
    
    async function validateMarkdown() {
      const content = getMarkdownContent()
      if (!content) {
        ElMessage.warning('Please provide markdown content first')
        return
      }
      
      try {
        // Use network store to validate markdown
        const success = await networkStore.parseMarkdown(content)
        if (success) {
          validationResult.value = { valid: true, errors: [], warnings: [] }
          ElMessage.success('Markdown format is valid!')
        } else {
          validationResult.value = { 
            valid: false, 
            errors: ['Failed to parse markdown'], 
            warnings: [] 
          }
          ElMessage.error('Markdown format has errors')
        }
      } catch (error) {
        validationResult.value = { 
          valid: false, 
          errors: [error.message], 
          warnings: [] 
        }
        ElMessage.error('Markdown format has errors: ' + error.message)
      }
    }
    
    function getValidationDescription() {
      if (!validationResult.value) return ''
      
      const { errors, warnings } = validationResult.value
      const parts = []
      
      if (errors.length > 0) {
        parts.push(`Errors: ${errors.join(', ')}`)
      }
      
      if (warnings.length > 0) {
        parts.push(`Warnings: ${warnings.join(', ')}`)
      }
      
      return parts.join(' | ')
    }
    
    function getPresetPreview(presetKey) {
      const preset = PRESET_NETWORKS[presetKey]
      if (!preset) return ''
      
      const lines = preset.content.split('\n').slice(0, 3)
      return lines.join(' → ') + '...'
    }
    
    function handleFileChange(file) {
      form.file = file
      
      // Read file content
      const reader = new FileReader()
      reader.onload = (e) => {
        form.fileContent = e.target.result
        validationResult.value = null // Reset validation when file changes
      }
      reader.onerror = () => {
        ElMessage.error('Failed to read file')
        form.fileContent = ''
      }
      reader.readAsText(file.raw)
    }
    
    function handleFileRemove() {
      form.file = null
      form.fileContent = ''
      validationResult.value = null
    }
    
    function handleCancel() {
      dialogVisible.value = false
      resetForm()
    }
    
    async function handleSubmit() {
      // Validate form
      try {
        await formRef.value.validate()
      } catch {
        ElMessage.error('Please fill in all required fields')
        return
      }
      
      // Get markdown content
      const content = getMarkdownContent()
      if (!content) {
        ElMessage.error('Please provide markdown content')
        return
      }
      
      // Update settings with selected values
      settingsStore.updateApiSettings({
        language: form.language,
        useCache: form.useCache
      })
      
      // Emit network data
      emit('network-loaded', {
        markdown: content,
        language: form.language,
        useCache: form.useCache,
        useLLM: form.useLLM
      })
      
      // Close dialog
      dialogVisible.value = false
      
      // Reset form
      resetForm()
    }
    
    function resetForm() {
      form.inputMethod = 'preset'
      form.markdownText = ''
      form.file = null
      form.fileContent = ''
      form.preset = 'heart'
      form.language = settingsStore.apiSettings.language
      form.useCache = settingsStore.apiSettings.useCache
      form.useLLM = true
      validationResult.value = null
      
      // Clear upload component
      if (uploadRef.value) {
        uploadRef.value.clearFiles()
      }
    }
    
    // Watch for input method changes to reset validation
    watch(() => form.inputMethod, () => {
      validationResult.value = null
    })
    
    // Watch for preset changes to reset validation
    watch(() => form.preset, () => {
      validationResult.value = null
    })
    
    // Watch for settings changes to update form
    watch(() => settingsStore.apiSettings, (newSettings) => {
      form.language = newSettings.language
      form.useCache = newSettings.useCache
    }, { deep: true })
    
    return {
      // Stores
      networkStore,
      settingsStore,
      
      // Refs
      formRef,
      uploadRef,
      
      // Reactive
      form,
      formRules,
      validationResult,
      
      // Computed
      dialogVisible,
      presetOptions,
      canValidate,
      canSubmit,
      
      // Methods
      handleFileChange,
      handleFileRemove,
      handleCancel,
      handleSubmit,
      validateMarkdown,
      getValidationDescription,
      getPresetPreview,
      
      // Icons
      UploadFilled,
      QuestionFilled
    }
  }
}
</script>

<style scoped>
.input-help {
  margin-top: 8px;
}

.file-preview {
  margin-top: 8px;
}

.preset-preview {
  margin-top: 8px;
}

.option-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.warning-text {
  margin-top: 8px;
}

.validation-summary {
  width: 100%;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

/* Custom upload styling */
:deep(.el-upload-dragger) {
  width: 100%;
}

:deep(.el-upload-dragger .el-icon--upload) {
  margin: 20px 0 16px;
  font-size: 40px;
  color: #c0c4cc;
}

/* Form item spacing */
.el-form-item {
  margin-bottom: 24px;
}

/* Radio group styling */
.el-radio-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .dialog-footer {
    flex-direction: column;
  }
  
  .el-radio-group {
    gap: 12px;
  }
}
</style>