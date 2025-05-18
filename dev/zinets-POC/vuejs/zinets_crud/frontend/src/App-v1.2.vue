<template>
  <div class="container">
    <h1>Chinese Character Manager</h1>
    
    <!-- Search Controls -->
    <div class="search-container">
      <el-form :inline="true" class="search-form">
        <el-form-item label="Character">
          <el-input
            v-model="searchParams.character"
            placeholder="字"
            clearable
            style="width: 60px"
          />
        </el-form-item>
        <el-form-item label="Meaning">
          <el-input
            v-model="searchParams.meaning"
            placeholder="Search meaning"
            clearable
            style="width: 200px"
          />
        </el-form-item>
        <el-form-item label="Provider">
          <el-select
            v-model="searchParams.llm_provider"
            placeholder="Select provider"
            clearable
            style="width: 200px"
          >
            <el-option
              v-for="provider in providers"
              :key="provider"
              :label="provider"
              :value="provider"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="Status">
          <el-select
            v-model="searchParams.is_active"
            placeholder="Select status"
            clearable
            style="width: 120px"
          >
            <el-option label="Active" value="Y" />
            <el-option label="Inactive" value="N" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            :icon="Search"
            @click="searchCharacters"
            :loading="tableLoading"
          >
            Search
          </el-button>
          <el-button :icon="Refresh" @click="resetSearch">
            Reset
          </el-button>
          <el-button type="success" :icon="Plus" @click="createNewCharacter">
            New Character
          </el-button>
        </el-form-item>
      </el-form>
    </div>
    
    <!-- Upper Panel: Character List -->
    <div class="upper-panel">
      <el-table
        :data="characters"
        style="width: 100%"
        @row-click="handleRowClick"
        v-loading="tableLoading"
        highlight-current-row
        empty-text="No characters found"
      >
        <el-table-column
          prop="character"
          label="Character"
          width="100"
          sortable
        />
        <el-table-column
          prop="pinyin"
          label="Pinyin"
          width="120"
          sortable
        />
        <el-table-column
          prop="meaning"
          label="Meaning"
          min-width="200"
          show-overflow-tooltip
        />
        <el-table-column
          prop="composition"
          label="Composition"
          min-width="200"
          show-overflow-tooltip
        />
        <el-table-column
          prop="phrases"
          label="Phrases"
          min-width="250"
          show-overflow-tooltip
        >
          <template #default="{ row }">
            <div v-html="row.phrases" />
          </template>
        </el-table-column>
        <el-table-column prop="llm_provider" label="Provider" width="120" sortable />
        <el-table-column prop="llm_model_name" label="Model" width="150" sortable />
        <el-table-column prop="is_active" label="Active" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_active === 'Y' ? 'success' : 'danger'">
              {{ row.is_active === 'Y' ? 'Yes' : 'No' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_best" label="Best" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_best === 'Y' ? 'success' : 'info'">
              {{ row.is_best === 'Y' ? 'Yes' : 'No' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- Pagination -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[5, 10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="totalCharacters"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>
    
    <!-- Lower Panel: Character Details -->
    <div class="lower-panel" v-loading="formLoading">
      <h2>
        {{ isCreating ? 'Create New Character' : 'Character Details' }}
      </h2>
      <el-form
        ref="characterFormRef"
        :model="currentCharacter"
        :rules="formRules"
        label-width="100px"
        label-position="left"
      >
        <!-- Row 1: Character, Pinyin, Provider, Model, Active, Best (6 compact fields) -->
        <el-row :gutter="15">
          <el-col :span="4">
            <el-form-item label="Character" prop="character">
              <el-input
                v-model="currentCharacter.character"
                :disabled="!isCreating"
                placeholder="字"
              />
            </el-form-item>
          </el-col>
          <el-col :span="4">
            <el-form-item label="Pinyin" prop="pinyin">
              <el-input
                v-model="currentCharacter.pinyin"
                placeholder="pinyin"
              />
            </el-form-item>
          </el-col>
          <el-col :span="4">
            <el-form-item label="Provider" prop="llm_provider">
              <el-select
                v-model="currentCharacter.llm_provider"
                :disabled="!isCreating"
                placeholder="Provider"
                style="width: 100%"
              >
                <el-option
                  v-for="provider in providers"
                  :key="provider"
                  :label="provider"
                  :value="provider"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="4">
            <el-form-item label="Model" prop="llm_model_name">
              <el-input
                v-model="currentCharacter.llm_model_name"
                :disabled="!isCreating"
                placeholder="model"
              />
            </el-form-item>
          </el-col>
          <el-col :span="4">
            <el-form-item label="Active">
              <el-select
                v-model="currentCharacter.is_active"
                placeholder="Status"
                style="width: 100%"
              >
                <el-option label="Active" value="Y" />
                <el-option label="Inactive" value="N" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="4">
            <el-form-item label="Best">
              <el-select
                v-model="currentCharacter.is_best"
                placeholder="Best"
                style="width: 100%"
              >
                <el-option label="Yes" value="Y" />
                <el-option label="No" value="N" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <!-- Row 2: Meaning, Composition, Phrases (3 columns) -->
        <el-row :gutter="15">
          <el-col :span="8">
            <el-form-item label="Meaning" prop="meaning">
              <el-input
                v-model="currentCharacter.meaning"
                type="textarea"
                :rows="4"
                placeholder="Enter character meaning"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="Composition" prop="composition">
              <el-input
                v-model="currentCharacter.composition"
                type="textarea"
                :rows="4"
                placeholder="Enter character composition/structure"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="Phrases" prop="phrases">
              <el-input
                v-model="currentCharacter.phrases"
                type="textarea"
                :rows="4"
                placeholder="Enter example phrases (HTML allowed for formatting)"
              />
            </el-form-item>
          </el-col>
        </el-row>
        
        <!-- Form Actions -->
        <div class="form-actions">
          <el-button
            type="primary"
            :icon="isCreating ? Plus : Edit"
            @click="saveCharacter"
            :disabled="!isFormChanged"
            :loading="saveLoading"
          >
            {{ isCreating ? 'Create' : 'Update' }}
          </el-button>
          <el-button :icon="Refresh" @click="cancelEdit">
            Cancel
          </el-button>
          <el-button
            v-if="!isCreating"
            type="danger"
            :icon="Delete"
            @click="confirmDelete"
          >
            Deactivate
          </el-button>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, watch, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Search,
  Refresh,
  Plus,
  Edit,
  Delete,
  Check,
  Close,
  Star,
  StarFilled,
} from '@element-plus/icons-vue'
import { characterService } from './services/api.js'

export default {
  name: 'App',
  components: {
    Search,
    Refresh,
    Plus,
    Edit,
    Delete,
    Check,
    Close,
    Star,
    StarFilled,
  },
  setup() {
    // Refs
    const characterFormRef = ref(null)
    
    // State
    const characters = ref([])
    const currentCharacter = ref({
      character: '',
      pinyin: '',
      meaning: '',
      composition: '',
      phrases: '',
      llm_provider: '',
      llm_model_name: '',
      timestamp: '',
      is_active: 'Y',
      is_best: 'Y',
    })
    const originalCharacter = ref({})
    const isCreating = ref(false)
    const tableLoading = ref(false)
    const formLoading = ref(false)
    const saveLoading = ref(false)
    
    // Pagination
    const currentPage = ref(1)
    const pageSize = ref(10)
    const totalCharacters = ref(0)
    
    // Search params
    const searchParams = reactive({
      character: '',
      meaning: '',
      llm_provider: '',
      is_active: '',
    })
    
    // Providers list
    const providers = ref(['Google', 'OpenAI', 'Anthropic', 'Claude'])
    
    // Form validation rules
    const formRules = {
      character: [
        {
          required: true,
          message: 'Character is required',
          trigger: 'blur',
        },
      ],
      pinyin: [
        {
          required: true,
          message: 'Pinyin is required',
          trigger: 'blur',
        },
      ],
      meaning: [
        {
          required: true,
          message: 'Meaning is required',
          trigger: 'blur',
        },
      ],
      llm_provider: [
        {
          required: true,
          message: 'Provider is required',
          trigger: 'change',
        },
      ],
      llm_model_name: [
        {
          required: true,
          message: 'Model name is required',
          trigger: 'blur',
        },
      ],
    }
    
    // Check if form has been changed
    const isFormChanged = computed(() => {
      if (isCreating.value) return true
      return JSON.stringify(currentCharacter.value) !== JSON.stringify(originalCharacter.value)
    })
    
    // Methods
    async function fetchCharacters() {
      tableLoading.value = true
      
      try {
        const params = {
          page: currentPage.value,
          page_size: pageSize.value,
          ...Object.fromEntries(
            Object.entries(searchParams).filter(([, value]) => value !== '')
          ),
        }
        
        const response = await characterService.getCharacters(params)
        characters.value = response.items
        totalCharacters.value = response.total
      } catch (error) {
        ElMessage.error(error.message || 'Failed to fetch characters')
        console.error('Fetch characters error:', error)
      } finally {
        tableLoading.value = false
      }
    }
    
    function handleRowClick(row) {
      isCreating.value = false
      formLoading.value = true
      
      // Clone the row data to currentCharacter
      currentCharacter.value = { ...row }
      originalCharacter.value = { ...row }
      
      formLoading.value = false
    }
    
    function createNewCharacter() {
      isCreating.value = true
      currentCharacter.value = {
        character: '',
        pinyin: '',
        meaning: '',
        composition: '',
        phrases: '',
        llm_provider: '',
        llm_model_name: '',
        timestamp: new Date().toISOString(),
        is_active: 'Y',
        is_best: 'Y',
      }
      // Clear form validation
      nextTick(() => {
        if (characterFormRef.value) {
          characterFormRef.value.clearValidate()
        }
      })
    }
    
    async function saveCharacter() {
      if (!characterFormRef.value) return
      
      try {
        // Validate form
        await characterFormRef.value.validate()
        
        saveLoading.value = true
        
        if (isCreating.value) {
          // Create new character
          await characterService.createCharacter(currentCharacter.value)
          ElMessage.success('Character created successfully')
        } else {
          // Update existing character
          const char = currentCharacter.value
          await characterService.updateCharacter(
            char.character,
            char.llm_provider,
            char.llm_model_name,
            char
          )
          ElMessage.success('Character updated successfully')
        }
        
        // Refresh data
        await fetchCharacters()
        
        // Reset creation mode
        isCreating.value = false
        
        // Update original character for comparison
        originalCharacter.value = { ...currentCharacter.value }
        
      } catch (error) {
        ElMessage.error(error.message || 'Operation failed')
        console.error('Save character error:', error)
      } finally {
        saveLoading.value = false
      }
    }
    
    function cancelEdit() {
      if (isCreating.value) {
        isCreating.value = false
        currentCharacter.value = { ...originalCharacter.value }
      } else {
        currentCharacter.value = { ...originalCharacter.value }
      }
      
      // Clear form validation
      nextTick(() => {
        if (characterFormRef.value) {
          characterFormRef.value.clearValidate()
        }
      })
    }
    
    function confirmDelete() {
      ElMessageBox.confirm(
        'Are you sure you want to deactivate this character? This action will mark it as inactive.',
        'Confirm Deactivation',
        {
          confirmButtonText: 'Deactivate',
          cancelButtonText: 'Cancel',
          type: 'warning',
          dangerouslyUseHTMLString: false,
        }
      )
        .then(() => {
          softDeleteCharacter()
        })
        .catch(() => {
          // User cancelled
        })
    }
    
    async function softDeleteCharacter() {
      try {
        formLoading.value = true
        
        const char = currentCharacter.value
        await characterService.deactivateCharacter(
          char.character,
          char.llm_provider,
          char.llm_model_name
        )
        
        ElMessage.success('Character deactivated successfully')
        
        // Refresh data
        await fetchCharacters()
        
        // Update current character to show deactivated status
        currentCharacter.value.is_active = 'N'
        originalCharacter.value.is_active = 'N'
        
      } catch (error) {
        ElMessage.error(error.message || 'Failed to deactivate character')
        console.error('Deactivate character error:', error)
      } finally {
        formLoading.value = false
      }
    }
    
    function searchCharacters() {
      currentPage.value = 1
      fetchCharacters()
    }
    
    function resetSearch() {
      Object.keys(searchParams).forEach((key) => {
        searchParams[key] = ''
      })
      currentPage.value = 1
      fetchCharacters()
    }
    
    function handleSizeChange(size) {
      pageSize.value = size
      fetchCharacters()
    }
    
    function handleCurrentChange(page) {
      currentPage.value = page
      fetchCharacters()
    }
    
    // Watch for search parameter changes
    watch(
      () => [searchParams.character, searchParams.meaning, searchParams.llm_provider, searchParams.is_active],
      () => {
        // Debounce search
        clearTimeout(searchCharacters.timeout)
        searchCharacters.timeout = setTimeout(() => {
          if (currentPage.value === 1) {
            fetchCharacters()
          } else {
            currentPage.value = 1
          }
        }, 500)
      },
      { deep: true }
    )
    
    // Initial data load
    onMounted(() => {
      fetchCharacters()
    })
    
    return {
      // Refs
      characterFormRef,
      
      // State
      characters,
      currentCharacter,
      originalCharacter,
      isCreating,
      tableLoading,
      formLoading,
      saveLoading,
      searchParams,
      providers,
      formRules,
      isFormChanged,
      
      // Pagination
      currentPage,
      pageSize,
      totalCharacters,
      
      // Methods
      fetchCharacters,
      handleRowClick,
      createNewCharacter,
      saveCharacter,
      cancelEdit,
      confirmDelete,
      searchCharacters,
      resetSearch,
      handleSizeChange,
      handleCurrentChange,
      
      // Icons
      Search,
      Refresh,
      Plus,
      Edit,
      Delete,
      Check,
      Close,
      Star,
      StarFilled,
    }
  },
}
</script>

<style scoped>
/* Component-specific styles */
.el-table :deep(.el-table__row) {
  cursor: pointer;
}

.el-table :deep(.el-table__row:hover) {
  background-color: #f5f7fa;
}

.form-actions {
  border-top: 1px solid #e9ecef;
  padding-top: 20px;
  margin-top: 20px;
}

/* Responsive adjustments */
@media (max-width: 1200px) {
  .el-col-4 {
    width: 33.33%;
  }
}

@media (max-width: 768px) {
  .el-col-4,
  .el-col-8 {
    width: 100%;
  }
  
  .search-form {
    display: block;
  }
  
  .search-form .el-form-item {
    display: block;
    margin-bottom: 15px;
  }
}
</style>
